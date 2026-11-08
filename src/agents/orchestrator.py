import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

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
    def __init__(self, use_docker: bool = False, max_debug_iterations: int = 4):
        # 1. Shared Infrastructure
        self.vector_db = VectorDatabase()
        self.retriever = LiteratureRetriever(self.vector_db)
        self.memory = ContextMemoryManager()
        self.multimodal_parser = MultimodalParser()
        self.reward_model = DiscoveryRewardModel()
        self.latex_generator = LatexPaperGenerator()
     # 2. Execution Sandbox
        if use_docker:
            self.sandbox = DockerSandbox()
        else:
            self.sandbox = SecureSandbox()

        # 3. RL Feedback Loop
        self.feedback_loop = SelfDebuggingFeedbackLoop(max_iterations=max_debug_iterations)

        # 4. Specialized Agents
        self.reviewer_agent = LiteratureReviewerAgent(self.vector_db)
        self.hypothesis_agent = HypothesisGeneratorAgent(self.retriever)
        self.code_agent = CodeExecutorAgent(self.sandbox, self.feedback_loop)
        self.critic_agent = CriticAgent()

        # 5. Telemetry and Audit Trail
        self.trace_logs: List[Dict[str, Any]] = []
        self.current_state = "IDLE"
