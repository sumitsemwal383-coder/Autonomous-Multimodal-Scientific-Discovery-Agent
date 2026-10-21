
import logging
from typing import List, Dict, Any, Optional

from config.settings import MAX_CONTEXT_TOKENS

logger = logging.getLogger(__name__)


class ContextMemoryManager:
    """Manages working memory and episodic interaction history."""

    def __init__(
        self,
        max_tokens: int = MAX_CONTEXT_TOKENS
    ):
        self.max_tokens = max_tokens

        # Memory stores
        self.working_memory: Dict[str, Any] = {}
        self.episodic_history: List[Dict[str, Any]] = []
        self.total_tokens_consumed = 0

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token usage using approximately four characters per token.
        This is a heuristic, not an exact tokenizer.
        """
        return max(1, len(text) // 4)

    def add_interaction(
        self,
        agent_role: str,
        action: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an agent interaction in episodic memory and track its
        estimated token consumption.
        """
        token_cost = self.estimate_tokens(content)
        self.total_tokens_consumed += token_cost

        entry = {
            "role": agent_role,
            "action": action,
            "content": content,
            "tokens": token_cost,
            "metadata": metadata or {}
        }

        self.episodic_history.append(entry)

        logger.info(
            "Interaction recorded: role=%s, action=%s, tokens=%d",
            agent_role,
            action,
            token_cost
        )

    def get_token_metrics(self) -> Dict[str, Any]:
        """Return basic token usage and episodic memory metrics."""
        active_tokens = sum(
            entry["tokens"] for entry in self.episodic_history
        )

        utilization = (
            (active_tokens / self.max_tokens) * 100
            if self.max_tokens > 0
            else 0.0
        )

        return {
            "total_tokens_consumed": self.total_tokens_consumed,
            "active_context_tokens": active_tokens,
            "max_context_tokens": self.max_tokens,
            "utilization_pct": round(utilization, 2),
            "episodes_retained": len(self.episodic_history)
        }
