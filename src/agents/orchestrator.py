"""
Scientific Discovery Orchestrator

Coordinates literature ingestion, RAG-grounded hypothesis generation,
sandboxed experiment execution, statistical critique, and LaTeX synthesis.
"""

import logging
import time
from typing import Any, Dict, List

from src.rag.vector_db import VectorDatabase
from src.rag.retriever import LiteratureRetriever
from src.sandbox.secure_sandbox import SecureSandbox
from src.sandbox.docker_sandbox import DockerSandbox
from src.rl.feedback_loop import SelfDebuggingFeedbackLoop
from src.rl.reward_model import DiscoveryRewardModel
from src.memory.context_manager import ContextMemoryManager
from src.ingestion.multimodal_parser import MultimodalParser
from src.synthesis.latex_generator import LatexPaperGenerator

from .literature_reviewer import LiteratureReviewerAgent
from .hypothesis_generator import HypothesisGeneratorAgent
from .code_executor_agent import CodeExecutorAgent
from .critic_agent import CriticAgent

logger = logging.getLogger(__name__)


class ScientificDiscoveryOrchestrator:
    """Run the end-to-end autonomous scientific discovery workflow."""

    def __init__(
        self,
        use_docker: bool = False,
        max_debug_iterations: int = 4,
    ):
        # Shared infrastructure
        self.vector_db = VectorDatabase()
        self.retriever = LiteratureRetriever(self.vector_db)
        self.memory = ContextMemoryManager()
        self.multimodal_parser = MultimodalParser()
        self.reward_model = DiscoveryRewardModel()
        self.latex_generator = LatexPaperGenerator()

        # Execution sandbox
        self.sandbox = DockerSandbox() if use_docker else SecureSandbox()

        # Feedback loop
        self.feedback_loop = SelfDebuggingFeedbackLoop(
            max_iterations=max_debug_iterations
        )

        # Agents
        self.reviewer_agent = LiteratureReviewerAgent(self.vector_db)
        self.hypothesis_agent = HypothesisGeneratorAgent(self.retriever)

        # Pass only the sandbox here. This is compatible with both the
        # original one-argument constructor and the updated optional
        # feedback_loop constructor of CodeExecutorAgent.
        self.code_agent = CodeExecutorAgent(self.sandbox)

        self.critic_agent = CriticAgent()

        self.trace_logs: List[Dict[str, Any]] = []
        self.current_state = "IDLE"

    def _record(self, step: str, status: str, details: str = "") -> None:
        """Append a dashboard-friendly execution trace entry."""
        self.trace_logs.append(
            {
                "timestamp": time.strftime("%H:%M:%S"),
                "step": step,
                "status": status,
                "details": details,
            }
        )
        self.current_state = status

    @staticmethod
    def _safe_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def run_discovery_cycle(
        self,
        research_topic: str,
        max_papers: int = 4,
        test_self_debug: bool = False,
        compile_pdf: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute one discovery cycle.

        `compile_pdf` defaults to False so the dashboard can still produce
        a .tex manuscript on machines without a LaTeX distribution.
        """
        started = time.time()
        self.trace_logs = []
        self.current_state = "RUNNING"

        literature_result: Dict[str, Any] = {}
        hypothesis_result: Dict[str, Any] = {}
        experiment_result: Dict[str, Any] = {}
        critic_result: Dict[str, Any] = {}
        latex_result: Dict[str, Any] = {}
        multimodal_figures: List[Dict[str, Any]] = []
        errors: List[str] = []

        # 1. Literature review and vector-store ingestion
        try:
            self._record("LITERATURE_REVIEW", "RUNNING", research_topic)
            literature_result = self.reviewer_agent.execute(
                {
                    "research_topic": research_topic,
                    "max_papers": max_papers,
                }
            )
            literature_result = self._safe_dict(literature_result)

            papers = literature_result.get("papers", [])
            self._record(
                "LITERATURE_REVIEW",
                "COMPLETED",
                f"Found {literature_result.get('papers_found', len(papers))} papers",
            )

            # Preserve visual evidence if the source pipelines provide it.
            raw_papers = literature_result.get("raw_papers", [])
            for paper in raw_papers:
                if isinstance(paper, dict):
                    for figure in paper.get("figures", []) or []:
                        if isinstance(figure, dict):
                            multimodal_figures.append(figure)

            if multimodal_figures:
                try:
                    self.multimodal_parser.ingest_visual_evidence(
                        multimodal_figures,
                        self.vector_db,
                        {"research_topic": research_topic},
                    )
                except Exception as exc:
                    logger.exception("Visual evidence ingestion failed")
                    errors.append(f"Visual ingestion: {exc}")

        except Exception as exc:
            logger.exception("Literature review failed")
            errors.append(f"Literature review: {exc}")
            self._record("LITERATURE_REVIEW", "FAILED", str(exc))

        # 2. Grounded hypothesis generation
        try:
            self._record("HYPOTHESIS_GENERATION", "RUNNING")
            hypothesis_result = self.hypothesis_agent.execute(
                {"research_topic": research_topic}
            )
            hypothesis_result = self._safe_dict(hypothesis_result)
            self._record(
                "HYPOTHESIS_GENERATION",
                "COMPLETED",
                "Hypothesis generated",
            )
        except Exception as exc:
            logger.exception("Hypothesis generation failed")
            errors.append(f"Hypothesis generation: {exc}")
            self._record("HYPOTHESIS_GENERATION", "FAILED", str(exc))

        hypothesis = self._safe_dict(
            hypothesis_result.get("hypothesis", {})
        )

        # 3. Sandboxed experiment execution
        try:
            self._record("CODE_EXECUTION", "RUNNING")
            experiment_result = self.code_agent.execute(
                {"hypothesis": hypothesis}
            )
            experiment_result = self._safe_dict(experiment_result)

            execution_status = experiment_result.get("status", "FAILED")
            self._record(
                "CODE_EXECUTION",
                "COMPLETED" if execution_status == "SUCCESS" else "FAILED",
                execution_status,
            )

            # The optional debug simulation is reported as a dashboard
            # trace marker. Actual automatic code rewriting is not performed
            # by the currently supplied feedback-loop implementation.
            if test_self_debug:
                execution_meta = self._safe_dict(
                    experiment_result.get("execution_result", {})
                )
                if execution_status != "SUCCESS":
                    debug_info = self.feedback_loop.analyze_execution_failure(
                        code=experiment_result.get("code", ""),
                        stderr=str(execution_meta.get("stderr", "")),
                        exit_code=int(execution_meta.get("exit_code", -1)),
                        security_violation=execution_meta.get(
                            "security_violation"
                        ),
                    )
                    experiment_result["debug_trace"] = [
                        {
                            "iteration": 1,
                            "failure_analysis": debug_info,
                        }
                    ]
                    experiment_result["debug_iterations_count"] = 1
                else:
                    experiment_result["debug_trace"] = []
                    experiment_result["debug_iterations_count"] = 0
        except Exception as exc:
            logger.exception("Code execution failed")
            errors.append(f"Code execution: {exc}")
            experiment_result = {
                "status": "FAILED",
                "code": "",
                "execution_result": {
                    "success": False,
                    "stdout": "",
                    "stderr": str(exc),
                    "exit_code": -1,
                    "duration": 0.0,
                    "sandbox_mode": "unknown",
                    "is_breakout_attempt": False,
                },
                "metrics": {},
                "debug_trace": [],
                "debug_iterations_count": 0,
            }
            self._record("CODE_EXECUTION", "FAILED", str(exc))

        # Normalize execution data for downstream agents and the dashboard.
        execution_meta = self._safe_dict(
            experiment_result.get("execution_result", {})
        )
        execution_meta.setdefault(
            "success", experiment_result.get("status") == "SUCCESS"
        )
        execution_meta.setdefault("stdout", "")
        execution_meta.setdefault("stderr", "")
        execution_meta.setdefault("exit_code", -1)
        execution_meta.setdefault("duration", 0.0)
        execution_meta.setdefault("sandbox_mode", "unknown")
        execution_meta.setdefault("is_breakout_attempt", False)

        metrics = self._safe_dict(experiment_result.get("metrics", {}))

        # 4. Statistical critique
        try:
            self._record("STATISTICAL_CRITIQUE", "RUNNING")
            critic_result = self.critic_agent.execute(
                {
                    "metrics": metrics,
                    "hypothesis": hypothesis,
                }
            )
            critic_result = self._safe_dict(critic_result)
            self._record(
                "STATISTICAL_CRITIQUE",
                "COMPLETED",
                str(critic_result.get("verdict", "No verdict")),
            )
        except Exception as exc:
            logger.exception("Statistical critique failed")
            errors.append(f"Statistical critique: {exc}")
            critic_result = {
                "status": "FAILED",
                "verdict": "NOT_EVALUATED",
                "is_significant": False,
                "estimated_power": 0.0,
                "critique": str(exc),
            }
            self._record("STATISTICAL_CRITIQUE", "FAILED", str(exc))

        # 5. LaTeX manuscript synthesis
        try:
            self._record("LATEX_SYNTHESIS", "RUNNING")
            literature_for_paper = dict(literature_result)
            literature_for_paper["citations"] = hypothesis_result.get(
                "citations_used",
                hypothesis.get("grounding_citations", []),
            )

            latex_result = self.latex_generator.compile_research_paper(
                hypothesis_data=hypothesis_result,
                experiment_data=experiment_result,
                critic_data=critic_result,
                literature_data=literature_for_paper,
                compile_pdf=compile_pdf,
            )
            latex_result = self._safe_dict(latex_result)
            latex_status = latex_result.get("status", "FAILED")
            self._record(
                "LATEX_SYNTHESIS",
                "COMPLETED" if latex_status != "FAILED" else "FAILED",
                str(latex_result.get("tex_path") or latex_result.get("errors", "")),
            )
        except Exception as exc:
            logger.exception("LaTeX synthesis failed")
            errors.append(f"LaTeX synthesis: {exc}")
            latex_result = {
                "status": "FAILED",
                "title": "Scientific Discovery Manuscript",
                "abstract": "",
                "tex_path": None,
                "pdf_path": None,
                "rendered_tex": "",
                "errors": [str(exc)],
            }
            self._record("LATEX_SYNTHESIS", "FAILED", str(exc))

        duration = round(time.time() - started, 3)

        # Approximate token telemetry from text handled in this local run.
        # This is not a billable-token measurement.
        telemetry_text = (
            research_topic
            + str(literature_result)
            + str(hypothesis_result)
        )
        estimated_context_tokens = max(1, len(telemetry_text) // 4)

        overall_status = (
            "SUCCESS"
            if experiment_result.get("status") == "SUCCESS"
            and critic_result.get("status") == "SUCCESS"
            and latex_result.get("status") != "FAILED"
            else "PARTIAL"
        )

        self._record(
            "DISCOVERY_CYCLE",
            overall_status,
            f"Completed in {duration} seconds",
        )

        return {
            "status": overall_status,
            "duration_seconds": duration,
            "estimated_cost_usd": 0.0,
            "telemetry": {
                "tokens": {
                    "active_context_tokens": estimated_context_tokens
                }
            },
            "trace_logs": self.trace_logs,
            "literature_review": {
                "literature_synthesis": literature_result.get(
                    "literature_synthesis", ""
                ),
                "research_gap": literature_result.get("research_gap", ""),
                "papers": literature_result.get("papers", []),
                "papers_found": literature_result.get("papers_found", 0),
                "indexed_count": literature_result.get("indexed_count", 0),
                "citations": hypothesis_result.get("citations_used", []),
            },
            "hypothesis_generation": hypothesis_result,
            "multimodal_figures": multimodal_figures,
            "code_execution": {
                **experiment_result,
                "execution_result": execution_meta,
                "metrics": metrics,
                "debug_trace": experiment_result.get("debug_trace", []),
                "debug_iterations_count": experiment_result.get(
                    "debug_iterations_count", 0
                ),
            },
            "critic_evaluation": critic_result,
            "latex_synthesis": latex_result,
            "errors": errors,
        }
