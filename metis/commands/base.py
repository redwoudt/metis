from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ToolContext:
    """Shared execution context passed through handlers and into Commands."""
    command: "ToolCommand"
    args: Dict[str, Any]
    user: Any
    metadata: Dict[str, Any] | None = None
    result: Any = None


class ToolCommand(ABC):
    """Base class for all tool commands."""

    name: str  # must be set by subclasses

    @abstractmethod
    def execute(self, context: ToolContext) -> Any:
        """Perform the actual tool action."""
        ...