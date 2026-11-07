
"""
Unit tests for Holdout Benchmark Evaluator.

Validates literature grounding, statistical rigor,
sandbox security, LaTeX synthesis and weighted scoring.
"""

import json
import pytest

from src.evaluation.benchmark_evaluator import BenchmarkEvaluator
# Adjust this import if your evaluator is stored in a different module.


@pytest.fixture
def benchmark_file(tmp_path):
    """Create a temporary holdout benchmark dataset."""
    file_path = tmp_path / "benchmark_ground_truth.json"

    benchmark_data = [
        {
            "id": "benchmark-001",
            "research_topic": "Scientific Discovery",
            "expected_result": "Expected research outcome"
        },
        {
            "id": "benchmark-002",
            "research_topic": "Machine Learning",
            "expected_result": "Expected ML outcome"
        }
    ]

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(benchmark_data, file)

    return file_path


@pytest.fixture
def evaluator(benchmark_file):
    """Create a benchmark evaluator using temporary data."""
    return BenchmarkEvaluator(benchmark_file=benchmark_file)


@pytest.fixture
def successful_discovery():
    """Provide a fully successful discovery result."""
    return {
        "research_topic": "Scientific Discovery",

        "hypothesis": {
            "grounding_citations": ["Ref_1", "Ref_2"],
            "is_grounded": True
        },

        "code_execution": {
            "status": "SUCCESS",
            "metrics": {
                "cohens_d": 0.8,
                "sample_size": 100,
                "ci_95_low": 0.2,
                "ci_95_high": 1.4
            },
            "execution_result": {
                "is_breakout_attempt": False
            }
        },

        "critic_evaluation": {
            "is_significant": True
        },

        "latex_synthesis": {
            "status": "SUCCESS",
            "tex_path": "output/scientific_discovery_paper.tex",
            "bib_path": "output/references.bib"
        }
    }


def test_load_holdout_benchmarks(evaluator):
    """Verify that holdout benchmark records are loaded."""
    assert len(evaluator.benchmarks) == 2
    assert evaluator.benchmarks[0]["id"] == "benchmark-001"


def test_evaluate_successful_discovery(
    evaluator,
    successful_discovery
):
    """Verify that a fully successful discovery receives 100."""
    result = evaluator.evaluate_discovery_run(
        successful_discovery
    )

    assert result["overall_score"] == 100.0
    assert result["grade"] == "A+ (Publication Ready)"

    assert result["dimensions"]["literature_grounding"] == 100.0
    assert result["dimensions"]["statistical_rigor"] == 100.0
    assert result["dimensions"]["sandbox_security_soundness"] == 100.0
    assert result["dimensions"]["latex_synthesis_fidelity"] == 100.0


def test_grounding_score_with_insufficient_citations(evaluator):
    """Verify that insufficient citations reduce grounding score."""
    discovery = {
        "hypothesis": {
            "grounding_citations": ["Ref_1"],
            "is_grounded": True
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    assert result["dimensions"]["literature_grounding"] == 70.0


def test_statistical_rigor_score(evaluator):
    """Verify statistical metrics contribute to the rigor score."""
    discovery = {
        "critic_evaluation": {
            "is_significant": True
        },
        "code_execution": {
            "metrics": {
                "cohens_d": 0.8,
                "sample_size": 100,
                "ci_95_low": 0.2,
                "ci_95_high": 1.4
            }
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    assert result["dimensions"]["statistical_rigor"] == 100.0


def test_confidence_interval_crossing_zero(evaluator):
    """Verify that a CI containing zero gets no CI points."""
    discovery = {
        "critic_evaluation": {
            "is_significant": True
        },
        "code_execution": {
            "metrics": {
                "cohens_d": 0.8,
                "sample_size": 100,
                "ci_95_low": -0.2,
                "ci_95_high": 1.4
            }
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    # 40 + 30 + 20 points; no 10 points for the CI.
    assert result["dimensions"]["statistical_rigor"] == 90.0


def test_sandbox_breakout_attempt(evaluator):
    """Verify that a breakout attempt receives zero security points."""
    discovery = {
        "code_execution": {
            "status": "SUCCESS",
            "execution_result": {
                "is_breakout_attempt": True
            }
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    assert result["dimensions"]["sandbox_security_soundness"] == 0.0


def test_failed_code_execution(evaluator):
    """Verify that failed execution receives partial security points."""
    discovery = {
        "code_execution": {
            "status": "FAILED",
            "execution_result": {
                "is_breakout_attempt": False
            }
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    assert result["dimensions"]["sandbox_security_soundness"] == 50.0


def test_latex_synthesis_score(evaluator):
    """Verify LaTeX output and bibliography scoring."""
    discovery = {
        "latex_synthesis": {
            "status": "SUCCESS",
            "tex_path": "output/scientific_discovery_paper.tex",
            "bib_path": "output/references.bib"
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    assert result["dimensions"]["latex_synthesis_fidelity"] == 100.0


def test_incomplete_latex_synthesis(evaluator):
    """Verify incomplete LaTeX output receives zero points."""
    discovery = {
        "latex_synthesis": {
            "status": "FAILED",
            "tex_path": "",
            "bib_path": ""
        }
    }

    result = evaluator.evaluate_discovery_run(discovery)

    assert result["dimensions"]["latex_synthesis_fidelity"] == 0.0


def test_weighted_overall_score(evaluator):
    """Verify the weighted scoring formula."""
    discovery = {
        "hypothesis": {
            "grounding_citations": ["Ref_1"],
            "is_grounded": True
        },
        "code_execution": {
            "status": "FAILED",
            "execution_result": {
                "is_breakout_attempt": False
            }
        },
        "critic_evaluation": {},
        "latex_synthesis": {}
    }

    result = evaluator.evaluate_discovery_run(discovery)

    # (70 * 0.25) + (0 * 0.35) + (50 * 0.20) + (0 * 0.20)
    assert result["overall_score"] == 27.5
    assert result["grade"] == "B (Revisions Required)"


def test_holdout_comparison_count(evaluator, successful_discovery):
    """Verify the number of loaded holdout records is reported."""
    result = evaluator.evaluate_discovery_run(
        successful_discovery
    )

    assert result["holdout_comparisons"] == 2


def test_missing_benchmark_file(tmp_path):
    """Verify that a missing benchmark file loads as an empty dataset."""
    missing_file = tmp_path / "missing_benchmarks.json"

    evaluator = BenchmarkEvaluator(
        benchmark_file=missing_file
    )

    assert evaluator.benchmarks == []
