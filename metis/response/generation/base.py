"""
Response Generation Strategy Base

This module defines the Strategy pattern abstraction for
controlling HOW the model is asked to generate a response.

It does NOT change prompts.
It does NOT decorate final output.
It ONLY controls generation parameters (temperature, max_tokens, etc.).

This keeps generation posture separate from rendering concerns.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class GeneratingModel(Protocol):
    """
    Protocol describing the minimal interface we expect
    from ModelManager.

    We intentionally depend only on `generate(...)`
    to avoid coupling to concrete adapters or vendors.
    """
    def generate(self, prompt: str, **kwargs: Any) -> str:
        ...


class ResponseGenerationStrategy(ABC):
    """
    Strategy interface.

    Concrete implementations define how the model
    should be invoked for a particular response style.
    """

    @abstractmethod
    def generate(
        self,
        model_manager: GeneratingModel,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """
        Generate a response using the supplied model manager.

        Parameters:
            model_manager: abstraction over model vendor
            prompt: fully rendered prompt string
            kwargs: additional generation parameters

        Returns:
            Model output as a string
        """
        raise NotImplementedError