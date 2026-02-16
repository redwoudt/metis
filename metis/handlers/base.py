from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from metis.commands.base import ToolContext


class ToolHandler(ABC):
    """Base class for all handlers in the execution chain."""

    def __init__(self, next_handler: Optional["ToolHandler"] = None):
        self._next = next_handler

    def handle(self, context: ToolContext) -> ToolContext:
        self._handle(context)
        if self._next:
            return self._next.handle(context)
        return context

    @abstractmethod
    def _handle(self, context: ToolContext) -> None:
        ...