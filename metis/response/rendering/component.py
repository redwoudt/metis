"""
Response Rendering Components

Defines the Decorator pattern base abstraction.

Rendering happens AFTER the model generates raw text.
"""

from abc import ABC, abstractmethod


class ResponseComponent(ABC):
    """
    Base abstraction for anything that can render
    a final response string.
    """

    @abstractmethod
    def render(self) -> str:
        raise NotImplementedError


class BaseResponse(ResponseComponent):
    """
    Wraps the raw model output.

    This is the concrete component that decorators wrap.
    """

    def __init__(self, content: str):
        self._content = content

    def render(self) -> str:
        return self._content