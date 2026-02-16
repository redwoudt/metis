from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, runtime_checkable

from ..model_client import ModelClient


@runtime_checkable
class RespondingModel(Protocol):
    """Lightweight interface for any model-like object used by RequestHandler.

    Invariants:
    - Must expose `respond(prompt: str, **kwargs) -> str`
    """

    def respond(self, prompt: str, **kwargs: Any) -> str: ...
