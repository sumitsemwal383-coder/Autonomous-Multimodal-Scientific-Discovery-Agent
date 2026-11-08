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
