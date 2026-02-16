# metis/components/session.py
"""Session object used by SessionManager.

A Session owns the ConversationEngine instance for a given user.

Some flows/tests construct sessions and engines directly (bypassing RequestHandler),
so we ensure the engine always has a `request_handler` attribute available for
states that reference it.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager


# We want Session.state to exist for all sessions, but we don't want hard import
# failures if state modules move. We'll best-effort import the default initial state.
try:
    # Common conventions (one of these likely exists in your codebase)
    from metis.states.greeting_state import GreetingState  # type: ignore
except Exception:  # pragma: no cover
    try:
        from metis.state.greeting_state import GreetingState  # type: ignore
    except Exception:  # pragma: no cover
        GreetingState = None  # type: ignore


class Session:
    """Holds conversation state for a single user."""

    DEFAULT_PREFERENCES: Dict[str, Any] = {
        "tone": "friendly",
        "persona": "",
        "context": "",
        "tool_output": "",
    }

    def __init__(
        self,
        user_id: Optional[str] = None,
        engine: Optional[ConversationEngine] = None,
        history: Optional[List[Any]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        request_handler: Any = None,
        state: Any = None,
    ):
        self.user_id = user_id

        # Create a default engine when one is not provided.
        # (Mainly used by tests and the in-memory SessionManager.)
        if engine is None:
            vendor = os.getenv("METIS_VENDOR", "mock")
            model = os.getenv("METIS_MODEL", "stub")
            client = ModelFactory.for_role(
                "analysis",
                {"vendor": vendor, "model": model, "policies": {}},
            )
            engine = ConversationEngine(
                model_manager=ModelManager(client),
                # IMPORTANT: ConversationEngine must remain backward compatible.
                # If it no longer accepts request_handler, it should accept and ignore it.
                request_handler=request_handler,
            )

        self.engine = engine

        # Ensure the engine always exposes a request_handler attribute.
        if not hasattr(self.engine, "request_handler"):
            self.engine.request_handler = None
        if request_handler is not None:
            self.engine.request_handler = request_handler

        # Conversation history
        self.history = history or []

        # Preferences
        merged_preferences: Dict[str, Any] = dict(self.DEFAULT_PREFERENCES)
        if preferences:
            merged_preferences.update(preferences)
        self.preferences = merged_preferences

        # Keep the engine's view of history/preferences aligned with the session.
        if hasattr(self.engine, "history"):
            self.engine.history = self.history
        if hasattr(self.engine, "preferences"):
            # engine.preferences may or may not exist / may not be a dict in some tests
            try:
                self.engine.preferences.update(self.preferences)
            except Exception:
                self.engine.preferences = dict(self.preferences)

        # ✅ Session.state must always exist.
        # Default to GreetingState() if available, else None.
        if state is not None:
            self.state = state
        else:
            self.state = GreetingState() if GreetingState is not None else None

        # Keep engine and session state aligned when possible.
        if hasattr(self.engine, "state"):
            try:
                self.engine.state = self.state
            except Exception:
                # Some engine implementations expose state differently; best-effort only.
                pass

    def set_state(self, state: Any) -> None:
        """Set the current conversation state and keep the engine in sync."""
        self.state = state
        if hasattr(self.engine, "state"):
            try:
                self.engine.state = state
            except Exception:
                pass

    def __setstate__(self, state_dict: Dict[str, Any]) -> None:
        """Restore state after unpickling and ensure required attributes exist."""
        self.__dict__.update(state_dict)

        # Ensure history/preferences always exist.
        if not hasattr(self, "history") or self.history is None:
            self.history = []
        if not hasattr(self, "preferences") or self.preferences is None:
            self.preferences = dict(self.DEFAULT_PREFERENCES)
        else:
            merged = dict(self.DEFAULT_PREFERENCES)
            try:
                merged.update(self.preferences)
            except Exception:
                pass
            self.preferences = merged

        # ✅ Session.state must always exist after restore.
        if not hasattr(self, "state"):
            try:
                default_state = GreetingState() if GreetingState is not None else None
            except Exception:
                default_state = None
            self.state = default_state

        # Best-effort: keep engine aligned with session after restore.
        if hasattr(self, "engine") and self.engine is not None:
            if not hasattr(self.engine, "history"):
                try:
                    self.engine.history = self.history
                except Exception:
                    pass
            else:
                try:
                    self.engine.history = self.history
                except Exception:
                    pass

            if not hasattr(self.engine, "preferences"):
                try:
                    self.engine.preferences = dict(self.preferences)
                except Exception:
                    pass
            else:
                try:
                    # engine.preferences may be a dict-like
                    self.engine.preferences.update(self.preferences)
                except Exception:
                    try:
                        self.engine.preferences = dict(self.preferences)
                    except Exception:
                        pass

            if hasattr(self.engine, "state"):
                try:
                    self.engine.state = self.state
                except Exception:
                    pass