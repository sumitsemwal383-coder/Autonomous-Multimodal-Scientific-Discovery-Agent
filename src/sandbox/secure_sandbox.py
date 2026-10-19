import ast
import logging

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
