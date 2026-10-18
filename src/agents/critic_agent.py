from typing import Dict, Any

import numpy as np
from scipy import stats

from .base_agent import BaseAgent
from config.settings import STATISTICAL_ALPHA_DEFAULT


class CriticAgent(BaseAgent):
    """Evaluates empirical results using statistical methods."""

    def __init__(self, alpha: float = STATISTICAL_ALPHA_DEFAULT):
        super().__init__(
            name="Empirical Statistical Critic",
            role="Statistical Critic Agent",
            description=(
                "Evaluates statistical significance, effect sizes, "
                "and confidence intervals for treatment gains."
            )
        )

        self.alpha = alpha

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a two-tailed one-sample t-test, calculate Cohen's d,
        and compute the confidence interval for mean treatment gain.

        Expected inputs:
            differences: paired treatment-minus-baseline differences
        """

        differences = np.asarray(
            inputs.get("differences", []),
            dtype=float
        )

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

        sample_size = len(differences)
        mean_difference = float(np.mean(differences))
        std_difference = float(np.std(differences, ddof=1))

        # Two-tailed Student's t-test
        t_statistic, p_value = stats.ttest_1samp(
            differences,
            popmean=0.0,
            alternative="two-sided"
        )

        # Cohen's dz effect size
        if std_difference == 0:
            cohens_d = (
                float("inf") if mean_difference > 0
                else float("-inf") if mean_difference < 0
                else 0.0
            )
        else:
            cohens_d = mean_difference / std_difference

        # Classify effect size
        magnitude = abs(cohens_d)

        if magnitude < 0.2:
            effect_magnitude = "Negligible"
        elif magnitude < 0.5:
            effect_magnitude = "Small"
        elif magnitude < 0.8:
            effect_magnitude = "Medium"
        else:
            effect_magnitude = "Large"

        # Compute the 95% confidence interval for the mean gain
        standard_error = stats.sem(differences)
        confidence_level = 0.95

        ci_low, ci_high = stats.t.interval(
            confidence_level,
            df=sample_size - 1,
            loc=mean_difference,
            scale=standard_error
        )

        # Determine statistical significance
        is_significant = bool(p_value < self.alpha)

        self.log_action(
            "STATISTICAL_ANALYSIS",
            (
                f"t={t_statistic:.4f}, p={p_value:.6f}, "
                f"Cohen's d={cohens_d:.4f}, "
                f"95% CI=[{ci_low:.4f}, {ci_high:.4f}]"
            )
        )

        self.execution_count += 1

        return {
            "status": "SUCCESS",
            "test": "Two-tailed Student's t-test",
            "t_statistic": float(t_statistic),
            "p_value": float(p_value),
            "alpha": self.alpha,
            "is_significant": is_significant,
            "cohens_d": float(cohens_d),
            "effect_magnitude": effect_magnitude,
            "mean_difference": mean_difference,
            "sample_size": sample_size,
            "confidence_level": confidence_level,
            "ci_95_low": float(ci_low),
            "ci_95_high": float(ci_high),
            "ci_95": [float(ci_low), float(ci_high)],
            "ci_excludes_zero": bool(ci_low > 0 or ci_high < 0)
        }
