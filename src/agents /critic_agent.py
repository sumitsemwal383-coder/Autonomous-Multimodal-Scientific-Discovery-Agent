from typing import Dict, Any

from .base_agent import BaseAgent
from config.settings import STATISTICAL_ALPHA_DEFAULT


class CriticAgent(BaseAgent):
    """
    Initializes the Statistical Critic Agent with a significance threshold.

    The default alpha value of 0.05 defines the significance level
    that will be used for future statistical hypothesis testing.
    """

    def __init__(self, alpha: float = STATISTICAL_ALPHA_DEFAULT):
        super().__init__(
            name="Empirical Statistical Critic",
            role="Statistical Critic Agent",
            description=(
                "Evaluates empirical results using statistical "
                "significance testing and other statistical measures."
            )
        )

        # Store the significance threshold
        self.alpha = alpha
