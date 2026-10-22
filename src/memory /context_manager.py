import logging
from typing import List, Dict, Any, Optional

from config.settings import MAX_CONTEXT_TOKENS, SLIDING_WINDOW_HISTORY

logger = logging.getLogger(__name__)


class ContextMemoryManager:
    """Manages episodic memory and recent interaction history."""

    def __init__(
        self,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        sliding_window_size: int = SLIDING_WINDOW_HISTORY
    ):
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")

        if sliding_window_size <= 0:
            raise ValueError("sliding_window_size must be greater than zero.")

        self.max_tokens = max_tokens
        self.sliding_window_size = sliding_window_size

        # Memory stores
        self.working_memory: Dict[str, Any] = {}
        self.episodic_history: List[Dict[str, Any]] = []
        self.total_tokens_consumed = 0

    def estimate_tokens(self, text: str) -> int:
        """Estimate token usage using approximately four characters per token."""
        return max(1, len(text) // 4)

    def add_interaction(
        self,
        agent_role: str,
        action: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an interaction and retain only the latest episodes."""

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

        # Day 9: Retain only the most recent interactions
        if len(self.episodic_history) > self.sliding_window_size:
            removed_count = (
                len(self.episodic_history) - self.sliding_window_size
            )

            self.episodic_history = self.episodic_history[
                -self.sliding_window_size:
            ]

            logger.info(
                "Sliding window applied: removed %d old episodes.",
                removed_count
            )

        logger.info(
            "Interaction recorded: role=%s, action=%s, tokens=%d",
            agent_role,
            action,
            token_cost
        )

    def get_recent_history(self) -> List[Dict[str, Any]]:
        """Return the currently retained recent interactions."""
        return list(self.episodic_history)

    def get_token_metrics(self) -> Dict[str, Any]:
        """Return token usage and active memory metrics."""

        active_tokens = sum(
            entry["tokens"] for entry in self.episodic_history
        )

        utilization = (
            (active_tokens / self.max_tokens) * 100
        )

        return {
            "total_tokens_consumed": self.total_tokens_consumed,
            "active_context_tokens": active_tokens,
            "max_context_tokens": self.max_tokens,
            "utilization_pct": round(utilization, 2),
            "episodes_retained": len(self.episodic_history),
            "sliding_window_size": self.sliding_window_size
        }
