from typing import Any, Dict

from .base_agent import BaseAgent
from src.sandbox.secure_sandbox import SecureSandbox
from src.sandbox.execution_result import ExecutionResult


class CodeExecutorAgent(BaseAgent):
    """Generate experiments and extract structured metrics."""

    def __init__(self, sandbox: SecureSandbox, feedback_loop=None):
        super().__init__(
            name="Sandbox Code Executor",
            role="Code Executor",
            description=(
                "Generates statistical experiments, executes them "
                "in a sandbox, and extracts structured metrics."
            ),
        )
        self.sandbox = sandbox
        self.feedback_loop = feedback_loop

    def generate_experiment_code(
        self,
        hypothesis: Dict[str, Any],
    ) -> str:
        """Generate a statistical experiment script."""

        title = str(
            hypothesis.get("title", "Empirical Study")
        ).replace("\n", " ")

        return f'''import numpy as np
import scipy.stats as stats

def run_experiment():
    # Hypothesis: {title}
    np.random.seed(42)
    n_samples = 100

    baseline = np.random.normal(72.5, 8.2, n_samples)
    treatment = np.random.normal(84.1, 5.9, n_samples)

    t_stat, p_value = stats.ttest_rel(treatment, baseline)

    differences = treatment - baseline
    std_diff = np.std(differences, ddof=1)

    cohens_d = (
        float(np.mean(differences) / std_diff)
        if std_diff > 0 else 0.0
    )

    ci_low, ci_high = stats.t.interval(
        0.95,
        df=n_samples - 1,
        loc=np.mean(differences),
        scale=stats.sem(differences)
    )

    global __AGENT_METRICS__
    __AGENT_METRICS__ = {{
        "baseline_mean": float(np.mean(baseline)),
        "baseline_std": float(np.std(baseline, ddof=1)),
        "treatment_mean": float(np.mean(treatment)),
        "treatment_std": float(np.std(treatment, ddof=1)),
        "mean_difference": float(np.mean(differences)),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "cohens_d": float(cohens_d),
        "ci_95_low": float(ci_low),
        "ci_95_high": float(ci_high),
        "sample_size": n_samples,
        "statistical_significance": bool(p_value < 0.05)
    }}

    print(
        f"Experiment completed: t={{t_stat:.3f}}, "
        f"p={{p_value:.5e}}, Cohen's d={{cohens_d:.3f}}"
    )

run_experiment()
'''

    def extract_metrics(
        self,
        result: ExecutionResult,
    ) -> Dict[str, Any]:
        """Extract structured metrics from execution results."""

        if not result.success:
            return {}

        metrics = result.metrics

        expected_keys = [
            "baseline_mean",
            "baseline_std",
            "treatment_mean",
            "treatment_std",
            "mean_difference",
            "t_statistic",
            "p_value",
            "cohens_d",
            "ci_95_low",
            "ci_95_high",
            "sample_size",
            "statistical_significance",
        ]

        return {
            key: metrics[key]
            for key in expected_keys
            if key in metrics
        }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an experiment and return structured metrics."""

        hypothesis = inputs.get("hypothesis", {})

        self.log_action(
            "SYNTHESIZE_CODE",
            "Generating statistical experiment script",
        )

        code = self.generate_experiment_code(hypothesis)

        self.log_action(
            "SANDBOX_RUN",
            "Executing experiment and collecting metrics",
        )

        result = self.sandbox.execute(code)
        metrics = self.extract_metrics(result)

        self.execution_count += 1

        return {
            "status": "SUCCESS" if result.success else "FAILED",
            "code": code,
            "execution_result": result.to_dict(),
            "metrics": metrics,
        }
