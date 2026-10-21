import ast
import logging
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from config.settings import SANDBOX_TIMEOUT_SECONDS
from .execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class ASTSecurityValidator(ast.NodeVisitor):
    """Detect unauthorized imports in Python code."""

    def __init__(self):
        self.violations = []
        self.is_breakout = False

        self.disallowed_modules = {
            "os", "subprocess", "ctypes", "socket", "shutil",
            "urllib", "requests", "http", "ftplib", "telnetlib",
            "paramiko", "pty", "fcntl", "pwd", "grp", "sys"
        }

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name.split(".")[0]
            if module in self.disallowed_modules:
                self.violations.append(
                    f"Unauthorized import: {alias.name}"
                )
                self.is_breakout = True

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module.split(".")[0]
            if module in self.disallowed_modules:
                self.violations.append(
                    f"Unauthorized from-import: {node.module}"
                )
                self.is_breakout = True

        self.generic_visit(node)
      
    def visit_Call(self, node):
        dangerous_functions = {
            "eval", "exec", "compile", "__import__",
            "breakpoint", "exit", "quit"
        }

        if (
            isinstance(node.func, ast.Name)
            and node.func.id in dangerous_functions
         ):
            self.violations.append(
                f"Unsafe function call: {node.func.id}()"
            )
            self.is_breakout = True

        # Detect obvious suspicious constant file paths.
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "open"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            path = node.args[0].value.lower()
            suspicious_parts = [
                "..", ".ssh", "system32", "/etc/", "root"
            ]

            if any(part in path for part in suspicious_parts):
                self.violations.append(
                    f"Suspicious file path: {node.args[0].value}"
                )
                self.is_breakout = True

        self.generic_visit(node)


def validate_code(code_str):
    """Parse and statically validate Python source code."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as error:
        return False, f"Syntax error: {error}", False

    validator = ASTSecurityValidator()
    validator.visit(tree)

    if validator.violations:
        return (
            False,
            "; ".join(validator.violations),
            validator.is_breakout,
        )

    return True, None, False
def visit_Attribute(self, node):
        dangerous_attributes = {
            "__class__",
            "__base__",
            "__bases__",
            "__subclasses__",
            "__globals__",
            "__builtins__",
            "__import__",
        }

        if node.attr in dangerous_attributes:
            self.violations.append(
                f"Reflective access blocked: {node.attr}"
            )
            self.is_breakout = True

        self.generic_visit(node)
class SecureSandbox:
    """Validate code and execute it in a separate Python process."""

    def __init__(self, timeout_seconds=SANDBOX_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds

    def execute(self, code_str):
        # Step 1: Validate source code.
        is_valid, violation, is_breakout = validate_code(code_str)

        if not is_valid:
            logger.warning("Sandbox validation failed: %s", violation)

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"SECURITY VIOLATION: {violation}",
                exit_code=-1,
                duration=0.0,
                metrics={},
                security_violation=violation,
                is_breakout_attempt=is_breakout,
                sandbox_mode="hardened_ast_subproc",
            )

        # Step 2: Create a temporary working directory.
        with tempfile.TemporaryDirectory(
            prefix="agent_sandbox_"
        ) as tmpdir:
            script_path = Path(tmpdir) / "experiment_run.py"

            instrumented_code = self._instrument_code(code_str)

            with open(script_path, "w", encoding="utf-8") as file:
                file.write(instrumented_code)

            start_time = time.time()

            try:
                # Step 3: Execute with a time limit.
                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env={
                        "PATH": str(Path(sys.executable).parent),
                        "PYTHONIOENCODING": "utf-8",
                        "PYTHONNOUSERSITE": "1",
                    },
                )

                duration = time.time() - start_time
                stdout = proc.stdout
                stderr = proc.stderr

                return ExecutionResult(
                    success=(proc.returncode == 0),
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=proc.returncode,
                    duration=duration,
                    metrics=self._extract_metrics(stdout),
                    security_violation=None,
                    is_breakout_attempt=False,
                    sandbox_mode="hardened_ast_subproc",
                )

            except subprocess.TimeoutExpired:
                duration = time.time() - start_time

                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=(
                        f"Execution timed out after "
                        f"{self.timeout_seconds} seconds."
                    ),
                    exit_code=-2,
                    duration=duration,
                    metrics={},
                    security_violation="Execution timeout exceeded",
                    is_breakout_attempt=False,
                    sandbox_mode="hardened_ast_subproc",
                )

            except Exception as error:
                duration = time.time() - start_time

                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Sandbox execution error: {error}",
                    exit_code=-3,
                    duration=duration,
                    metrics={},
                    security_violation=str(error),
                    is_breakout_attempt=False,
                    sandbox_mode="hardened_ast_subproc",
                )

    def _instrument_code(self, code):
        """Append a footer to export experiment metrics."""
        footer = """
import json

if '__AGENT_METRICS__' in locals():
    print('__AGENT_METRICS__:' + json.dumps(__AGENT_METRICS__))
"""
        return code + "\n" + footer

    def _extract_metrics(self, stdout):
        """Extract structured metrics from process output."""
        metrics = {}

        for line in stdout.splitlines():
            if line.startswith("__AGENT_METRICS__:"):
                try:
                    data = json.loads(
                        line.split(":", 1)[1].strip()
                    )
                    if isinstance(data, dict):
                        metrics.update(data)
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Could not parse metrics output")

        return metrics
