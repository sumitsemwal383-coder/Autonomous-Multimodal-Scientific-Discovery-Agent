
"""
Statistical Critic Agent

Implements two-tailed Student's t-test to evaluate the statistical
significance of empirical results produced by the Code Executor agent.
"""

from typing import Dict, Any
from scipy import stats

from .base_agent import BaseAgent
from config.settings import STATISTICAL_ALPHA_DEFAULT


class CriticAgent(BaseAgent):
    """
    Evaluates empirical results using statistical hypothesis testing.
    """

    def __init__(self, alpha: float = STATISTICAL_ALPHA_DEFAULT):
        super().__init__(
            name="Empirical Statistical Critic",
            role="Statistical Critic Agent",
            description=(
                "Evaluates empirical results using statistical "
                "significance testing."
            )
        )

        self.alpha = alpha

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a two-tailed one-sample t-test on the supplied differences.

        Expected inputs:
            differences: list of paired treatment-minus-baseline differences
        """

        differences = inputs.get("differences", [])

        if len(differences) < 2:
            return {
                "status": "ERROR",
                "message": "At least two observations are required for a t-test."
            }

        # Calculate the two-tailed one-sample Student's t-test
        t_statistic, p_value = stats.ttest_1samp(
            differences,
            popmean=0.0,
            alternative="two-sided"
        )

        # Determine statistical significance
        is_significant = p_value < self.alpha

        # Record the statistical audit
        self.log_action(
            "T_TEST",
            (
                f"Two-tailed t-test: t={t_statistic:.4f}, "
                f"p={p_value:.6f}, alpha={self.alpha}"
            )
        )

        self.execution_count += 1

        return {
            "status": "SUCCESS",
            "test": "Two-tailed Student's t-test",
            "t_statistic": round(float(t_statistic), 4),
            "p_value": float(p_value),
            "alpha": self.alpha,
            "is_significant": bool(is_significant),
            "verdict": (
                "STATISTICALLY_SIGNIFICANT"
                if is_significant
                else "NOT_STATISTICALLY_SIGNIFICANT"
            )
        }
