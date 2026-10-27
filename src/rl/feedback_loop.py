import re
import logging
from typing import Dict, Any, List, Optional
from .reward_model import DiscoveryRewardModel

logger = logging.getLogger(__name__)

class SelfDebuggingFeedbackLoop:
    def __init__(self, max_iterations: int = 4):
        self.max_iterations = max_iterations
        self.reward_model = DiscoveryRewardModel()
        self.history: List[Dict[str, Any]] = []

    def analyze_execution_failure(self, code: str, stderr: str, exit_code: int, security_violation: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses runtime errors and produces structured debugging critique.
        """
        if security_violation:
            return {
                "error_type": "SecurityBreakoutViolation",
                "message": security_violation,
                "culprit_hint": "Code attempted an unauthorized system call or forbidden module import.",
                "actionable_fix": "Rewrite code strictly using allowed scientific packages (numpy, scipy, pandas, sklearn). Remove all OS, socket, subprocess, and dangerous eval/exec calls."
            }

        # Analyze standard Python errors from stderr
        if "SyntaxError" in stderr:
            match = re.search(r"line (\d+)", stderr)
            line_no = match.group(1) if match else "unknown"
            return {
                "error_type": "SyntaxError",
                "message": stderr.strip().splitlines()[-1],
                "culprit_hint": f"Syntax error near line {line_no}.",
                "actionable_fix": "Verify parentheses, indentation, and variable assignments in Python 3 syntax."
            }
        elif "ZeroDivisionError" in stderr:
            return {
                "error_type": "ZeroDivisionError",
                "message": "Division by zero encountered in calculation.",
                "culprit_hint": "Denominator evaluated to 0 (e.g., standard deviation was 0 or sample size was 0).",
                "actionable_fix": "Add an epsilon (e.g. + 1e-8) or clamp denominator values before division."
            }
