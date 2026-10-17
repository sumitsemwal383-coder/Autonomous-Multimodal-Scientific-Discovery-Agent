from typing import Dict, Any
from scipy import stats
import numpy as np

from .base_agent import BaseAgent
from config.settings import STATISTICAL_ALPHA_DEFAULT


class CriticAgent(BaseAgent):
    """Evaluates empirical results using statistical methods."""

    def __init__(self, alpha: float = STATISTICAL_ALPHA_DEFAULT):
        super().__init__(
            name="Empirical Statistical Critic",
            role="Statistical Critic Agent",
            description=(
                "Evaluates statistical significance and "
                "standardized effect sizes."
            )
        )

        self.alpha = alpha

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a two-tailed one-sample t-test and calculate Cohen's d.

        Expected inputs:
            differences: list of paired treatment-minus-baseline differences
        """

        differences = np.asarray(inputs.get("differences", []), dtype=float)

        # Validate input data
        if (
            differences.ndim != 1
            or len(differences) < 2
            or not np.all(np.isfinite(differences))
        ):
            return {
                "status": "ERROR",
                "message": (
                    "Provide at least two finite numerical differences."
                )
            }

        # Two-tailed Student's t-test
        t_statistic, p_value = stats.ttest_1samp(
            differences,
            popmean=0.0,
            alternative="two-sided"
        )

        # Standardized Cohen's d for paired differences (d_z)
        mean_difference = np.mean(differences)
        std_difference = np.std(differences, ddof=1)

        if std_difference == 0:
            cohens_d = (
                float("inf") if mean_difference > 0
                else float("-inf") if mean_difference < 0
                else 0.0
            )
        else:
            cohens_d = mean_difference / std_difference

        # Interpret the absolute effect size
        magnitude = abs(cohens_d)

        if magnitude < 0.2:
            effect_magnitude = "Negligible"
        elif magnitude < 0.5:
            effect_magnitude = "Small"
        elif magnitude < 0.8:
            effect_magnitude = "Medium"
        else:
            effect_magnitude = "Large"

        is_significant = p_value < self.alpha

        self.log_action(
            "STATISTICAL_ANALYSIS",
            (
                f"t={t_statistic:.4f}, p={p_value:.6f}, "
                f"Cohen's d={cohens_d:.4f}"
            )
        )

        self.execution_count += 1

        return {
            "status": "SUCCESS",
            "test": "Two-tailed Student's t-test",
            "t_statistic": float(t_statistic),
            "p_value": float(p_value),
            "alpha": self.alpha,
            "is_significant": bool(is_significant),
            "cohens_d": float(cohens_d),
            "effect_magnitude": effect_magnitude,
            "mean_difference": float(mean_difference),
            "sample_size": len(differences)
        }
