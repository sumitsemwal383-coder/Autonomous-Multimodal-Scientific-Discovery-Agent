
"""
Statistical Critic Agent

Evaluates empirical results using a two-tailed Student's t-test,
Cohen's d effect size, 95% confidence intervals, and statistical
power estimation to help guard against Type II (beta) errors.
"""

from typing import Dict, Any

import numpy as np
from scipy import stats

from .base_agent import BaseAgent
from config.settings import (
    STATISTICAL_ALPHA_DEFAULT,
    MIN_STATISTICAL_POWER,
)


class CriticAgent(BaseAgent):
    """Evaluates empirical results using statistical methods."""

    def __init__(self, alpha: float = STATISTICAL_ALPHA_DEFAULT):
        super().__init__(
            name="Empirical Statistical Critic",
            role="Statistical Critic Agent",
            description=(
                "Evaluates statistical significance, effect sizes, "
                "confidence intervals, and statistical power."
            )
        )

        if not 0 < alpha < 1:
            raise ValueError("Alpha must be between 0 and 1.")

        self.alpha = alpha

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a two-tailed one-sample t-test on paired differences.

        Expected inputs:
            differences: treatment-minus-baseline differences

        Statistical power is estimated from the observed Cohen's dz.
        """

        try:
            differences = np.asarray(
                inputs.get("differences", []),
                dtype=float
            )
        except (TypeError, ValueError):
            return {
                "status": "ERROR",
                "message": "Differences must be numerical values."
            }

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

        # Day 3: Two-tailed Student's t-test
        t_statistic, p_value = stats.ttest_1samp(
            differences,
            popmean=0.0,
            alternative="two-sided"
        )

        # Day 4: Cohen's dz effect size
        if std_difference == 0:
            cohens_d = (
                float("inf") if mean_difference > 0
                else float("-inf") if mean_difference < 0
                else 0.0
            )
        else:
            cohens_d = mean_difference / std_difference

        magnitude = abs(cohens_d)

        if magnitude < 0.2:
            effect_magnitude = "Negligible"
        elif magnitude < 0.5:
            effect_magnitude = "Small"
        elif magnitude < 0.8:
            effect_magnitude = "Medium"
        else:
            effect_magnitude = "Large"

        # Day 5: 95% confidence interval for mean treatment gain
        standard_error = stats.sem(differences)

        ci_low, ci_high = stats.t.interval(
            confidence=0.95,
            df=sample_size - 1,
            loc=mean_difference,
            scale=standard_error
        )

        ci_excludes_zero = bool(ci_low > 0 or ci_high < 0)

        # Day 6: Statistical power and Type II error estimation
        # Power = P(reject H0 | specified effect is true)
        degrees_freedom = sample_size - 1

        if std_difference == 0:
            # Handle constant differences without infinite noncentrality.
            estimated_power = (
                1.0 if mean_difference != 0 else self.alpha
            )
        else:
            critical_t = stats.t.ppf(
                1 - self.alpha / 2,
                df=degrees_freedom
            )

            noncentrality = abs(cohens_d) * np.sqrt(sample_size)

            estimated_power = (
                stats.nct.cdf(
                    -critical_t,
                    df=degrees_freedom,
                    nc=noncentrality
                )
                + stats.nct.sf(
                    critical_t,
                    df=degrees_freedom,
                    nc=noncentrality
                )
            )

            estimated_power = float(
                np.clip(estimated_power, 0.0, 1.0)
            )

        # Beta is the estimated probability of a Type II error
        estimated_beta = 1.0 - estimated_power

        power_adequate = (
            estimated_power >= MIN_STATISTICAL_POWER
        )

        is_significant = bool(
            np.isfinite(p_value) and p_value < self.alpha
        )

        # Guard against treating underpowered results as conclusive
        if is_significant and ci_excludes_zero and power_adequate:
            verdict = "CONFIRMED_STATISTICALLY_SIGNIFICANT"
        elif is_significant and not power_adequate:
            verdict = "INCONCLUSIVE_UNDERPOWERED"
        else:
            verdict = "REJECTED_INSIGNIFICANT"

        self.log_action(
            "STATISTICAL_ANALYSIS",
            (
                f"t={t_statistic:.4f}, p={p_value:.6f}, "
                f"d={cohens_d:.4f}, "
                f"power={estimated_power:.3f}, "
                f"beta={estimated_beta:.3f}"
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
            "confidence_level": 0.95,
            "ci_95_low": float(ci_low),
            "ci_95_high": float(ci_high),
            "ci_95": [float(ci_low), float(ci_high)],
            "ci_excludes_zero": ci_excludes_zero,
            "estimated_power": round(estimated_power, 4),
            "estimated_beta": round(estimated_beta, 4),
            "minimum_required_power": MIN_STATISTICAL_POWER,
            "power_adequate": power_adequate,
            "verdict": verdict,
        }
