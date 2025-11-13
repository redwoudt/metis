import logging
from typing import Any, Optional

from metis.states.greeting import GreetingState  # initial conversation state
from metis.memory.snapshot import ConversationSnapshot  # Memento for snapshot/restore
from metis.models.model_client import ModelClient

logger = logging.getLogger(__name__)


class ConversationEngine:
    """
    ConversationEngine plays two roles:
    - State pattern context: it holds the current conversation state and delegates behavior to it.
    - Memento originator: it can snapshot and restore its internal state.

    In the updated architecture, it also collaborates with the Bridge:
    - It does NOT talk to provider SDKs directly.
    - Instead, it calls a ModelManager (the Bridge implementor), which wraps a
      provider-specific adapter (the Adapter pattern).

    Fix 3:
    - Maintain a `model` attribute synchronized with ModelManager.get_model().
    - Preserve the model_manager reference across snapshots (tests expect it).
    - Refresh the model pointer after restore to avoid stale or None values.
    """

    def __init__(self, model_manager):
        # --- State Pattern Context ---
        self.state = GreetingState()   # initial state
        self.history = []              # conversation transcript

        # Conversation preferences / session-level hints
        self.preferences = {
            "tone": "friendly",
            "persona": "",
            "context": "",
            "tool_output": "",
        }

        # --- Bridge Collaborator (ModelManager) ---
        self.model_manager = model_manager

        # Expose the active ModelClient for debugging/tests
        self.model: Optional[Any] = None
        if hasattr(self.model_manager, "get_model"):
            try:
                self.model = self.model_manager.get_model()
            except Exception:
                logger.debug(
                    "[ConversationEngine] model_manager.get_model() failed during __init__",
                    exc_info=True,
                )

        logger.debug(
            "[ConversationEngine] Initialized with GreetingState, "
            "empty history, preferences=%s, model_manager=%s",
            self.preferences,
            type(model_manager).__name__,
        )

    # ---------------------------------------------------------------------
    # Internal utilities
    # ---------------------------------------------------------------------
    def _refresh_model_ref(self) -> None:
        """Keep self.model synchronized with the current ModelManager."""
        if hasattr(self.model_manager, "get_model"):
            try:
                self.model = self.model_manager.get_model()
            except Exception:
                logger.debug(
                    "[ConversationEngine] model_manager.get_model() failed in _refresh_model_ref",
                    exc_info=True,
                )

    def get_model(self) -> ModelClient | None:
            """
            Public accessor used by tests to verify the active ModelClient.
            """
            self._refresh_model_ref()
            if self.model_manager is None:
                return None
            return self.model_manager.model_client

    # ---------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------
    def set_state(self, new_state):
        """Transition to a new conversation state."""
        logger.debug(
            "[ConversationEngine] Transitioning to new state: %s",
            new_state.__class__.__name__,
        )
        self.state = new_state

    # ---------------------------------------------------------------------
    # Dialogue and model interaction
    # ---------------------------------------------------------------------
    def respond(self, user_input: str) -> str:
        """
        High-level entry point for user messages.
        Delegates to the current state’s `respond()` method,
        which may internally call `generate_with_model()`.
        """
        logger.debug(
            "[ConversationEngine] Calling respond on state: %s with user_input='%s'",
            self.state.__class__.__name__,
            user_input,
        )

        response = self.state.respond(self, user_input)

        # Always coerce to string
        if response is None:
            logger.warning(
                "[ConversationEngine] State %s returned None; coercing to empty string",
                self.state.__class__.__name__,
            )
            response = ""

        self.history.append(response)
        logger.debug(
            "[ConversationEngine] Response appended to history. Total entries: %d",
            len(self.history),
        )
        return response

    def generate_with_model(self, prompt: str) -> str:
        """
        Bridge hook:
        States use this to delegate generation to the model layer (ModelManager).
        Ensures consistent interaction with adapters via the Bridge abstraction.
        """
        self._refresh_model_ref()
        logger.debug(
            "[ConversationEngine] Delegating prompt to ModelManager: %r",
            prompt[:200],
        )

        try:
            generated = self.model_manager.generate(prompt)
        except Exception as e:
            logger.error("[ConversationEngine] ModelManager.generate failed: %s", e)
            generated = ""

        # Normalize output to string
        if isinstance(generated, dict):
            generated = generated.get("text", "")
        elif not isinstance(generated, str):
            generated = str(generated or "")

        logger.debug(
            "[ConversationEngine] ModelManager returned text of length %d",
            len(generated) if generated else 0,
        )
        return generated

    def set_model_manager(self, model_manager):
        """
        Allows runtime replacement of the model_manager (e.g., for task-specific switching).
        Keeps model reference fresh.
        """
        logger.debug(
            "[ConversationEngine] Updating model_manager to %s",
            type(model_manager).__name__,
        )
        self.model_manager = model_manager
        self._refresh_model_ref()

    # ---------------------------------------------------------------------
    # Memento pattern: snapshot / restore
    # ---------------------------------------------------------------------
    def create_snapshot(self):
        """
        Create a deep snapshot of the engine’s current internal state.
        Includes state, history, preferences, and a reference to the model_manager.
        """
        snapshot = ConversationSnapshot(self.__dict__)

        logger.debug("[ConversationEngine] Snapshot created")
        return snapshot

    def restore_snapshot(self, snapshot):
        """
        Restore the engine’s state from a given snapshot.

        The snapshot should fully roll back the engine's internal state,
        including the model_manager, so that any adapter/model changes made
        after the snapshot are undone.
        """
        state_data = snapshot.get_state()

        # Restore full internal state, including model_manager
        self.__dict__.update(state_data)

        # Refresh the model reference for safety
        self._refresh_model_ref()
        logger.debug("[ConversationEngine] State restored from snapshot")