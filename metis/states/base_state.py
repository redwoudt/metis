# states/base_state.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ConversationState(ABC):
    """
    Abstract base class for all conversation states.
    Each state represents one phase in the conversation flow
    (e.g. Greeting, Clarifying, Executing, Summarizing).

    States should NOT call model APIs directly.
    Instead, they should ask the ConversationEngine to do that via
    engine.generate_with_model(...), which routes through the Bridge
    (ConversationEngine -> ModelManager) and the Adapter for the
    current provider.
    """

    @abstractmethod
    def respond(self, engine, user_input: str) -> str:
        """
        Handle user input and return a response.
        May trigger state transitions via engine.set_state().

        :param engine: The ConversationEngine context.
        :param user_input: The latest user input string.
        :return: A response string from the assistant.
        """
        raise NotImplementedError

    def replace(self, *args: Any, **changes: Any) -> "ConversationState":
        """
        Backward-compatible "replace" helper.

        Some older code/tests call:
            state.replace(old_state, new_state)
        while newer code calls:
            state.replace(foo="bar")

        Base states are typically stateless, so the default behavior is:
        - ignore positional args entirely
        - return self (or apply keyword changes if a subclass overrides)
        """
        _ = args  # intentionally ignored for backward compatibility
        _ = changes  # base class is immutable/stateless by default
        return self