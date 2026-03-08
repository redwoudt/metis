from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ToolContext:
    """
    Shared execution context passed through handlers and into commands.

    Why this exists:
    - commands need more than raw args
    - handlers may enrich execution with metadata, audit info, or results
    - some commands now need access to shared backend services such as:
        - scheduler
        - clock
        - quota service
        - audit logger

    """
    command: "ToolCommand"
    args: Dict[str, Any]
    user: Any
    metadata: Dict[str, Any] | None = None
    result: Any = None
    services: Any = None


class ToolCommand(ABC):
    """
    Base class for all tool commands.

    Each command encapsulates a single unit of application behavior behind a
    common interface, which is the core idea of the Command Pattern.
    """

    name: str  # must be set by subclasses

    @abstractmethod
    def execute(self, context: ToolContext) -> Any:
        """
        Execute the command using the supplied context.
        """
        ...