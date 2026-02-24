"""
Concrete Response Generation Strategies

Each class represents a different generation posture.

These strategies modify generation parameters,
not prompt structure.

They rely on ModelManager to handle vendor-specific
mapping of arguments.
"""

from typing import Any
from .base import ResponseGenerationStrategy, GeneratingModel


class DefaultStrategy(ResponseGenerationStrategy):
    """
    Pass-through strategy.

    Used when no specific style is requested.
    """

    def generate(
        self,
        model_manager: GeneratingModel,
        prompt: str,
        **kwargs: Any
    ) -> str:
        return model_manager.generate(prompt, **kwargs)


class ConciseStrategy(ResponseGenerationStrategy):
    """
    Produces shorter responses.
    """

    def generate(self, model_manager, prompt, **kwargs):
        # Set defaults only if not already provided
        kwargs.setdefault("max_tokens", 120)
        return model_manager.generate(prompt, **kwargs)


class DetailedStrategy(ResponseGenerationStrategy):
    """
    Produces longer, more thorough responses.
    """

    def generate(self, model_manager, prompt, **kwargs):
        kwargs.setdefault("max_tokens", 800)
        return model_manager.generate(prompt, **kwargs)


class CreativeStrategy(ResponseGenerationStrategy):
    """
    Encourages higher variance and expressive output.
    """

    def generate(self, model_manager, prompt, **kwargs):
        kwargs.setdefault("temperature", 0.9)
        kwargs.setdefault("max_tokens", 600)
        return model_manager.generate(prompt, **kwargs)


class AnalyticalStrategy(ResponseGenerationStrategy):
    """
    Encourages lower temperature and structured reasoning.
    """

    def generate(self, model_manager, prompt, **kwargs):
        kwargs.setdefault("temperature", 0.2)
        kwargs.setdefault("max_tokens", 700)
        return model_manager.generate(prompt, **kwargs)