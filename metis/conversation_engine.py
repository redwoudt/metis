import logging
from metis.states.greeting import GreetingState  # initial conversation state
from metis.memory.snapshot import ConversationSnapshot  # Memento for snapshot/restore

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
    """

    def __init__(self, model_manager):
        # State pattern
        self.state = GreetingState()  # starting state
        self.history = []             # conversation transcript / outputs

        # Session / turn preferences and context hints
        # Pre-populate expected keys so states can safely access them without KeyError.
        self.preferences = {
            "tone": "friendly",
            "persona": "",
            "context": "",
            "tool_output": "",
        }

        # Bridge implementor (injected)
        self.model_manager = model_manager

        logger.debug(
            "[ConversationEngine] Initialized with GreetingState, "
            "empty history, preferences=%s, model_manager=%s",
            self.preferences,
            type(model_manager).__name__,
        )

    def set_state(self, new_state):
        """
        Transition to a new conversation state.
        Each state decides how to respond to input,
        but they all share this engine context.
        """
        logger.debug(
            "[ConversationEngine] Transitioning to new state: %s",
            new_state.__class__.__name__,
        )
        self.state = new_state

    def respond(self, user_input: str) -> str:
        """
        High-level entry point: ask the *current state* to handle the input.

        The state will typically:
        - interpret the user_input,
        - optionally call engine.generate_with_model() to get LLM output,
        - return a response string.

        We append that response into history for traceability.
        """
        logger.debug(
            "[ConversationEngine] Calling respond on state: %s with user_input='%s'",
            self.state.__class__.__name__,
            user_input,
        )

        response = self.state.respond(self, user_input)

        # Defensive: ensure we always work with a string
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
        States call this instead of talking to OpenAI/Anthropic/etc. directly.

        Under the hood, this delegates to the injected ModelManager,
        which in turn delegates to the correct ModelClient adapter.

        This is the key point where Adapter + Bridge meet.
        """
        logger.debug(
            "[ConversationEngine] Delegating prompt to ModelManager: %r",
            prompt[:200],
        )
        generated = self.model_manager.generate(prompt)
        logger.debug(
            "[ConversationEngine] ModelManager returned text of length %d",
            len(generated) if generated else 0,
        )
        return generated

    def set_model_manager(self, model_manager):
        """
        Allows RequestHandler to update which model manager we're using
        mid-session (e.g. swap summarizer vs planner model, fallback provider, etc.).
        """
        logger.debug(
            "[ConversationEngine] Updating model_manager to %s",
            type(model_manager).__name__,
        )
        self.model_manager = model_manager

    # --- Memento support -------------------------------------------------

    def create_snapshot(self):
        """
        Create a deep snapshot of the engine's current internal state for rollback.
        We include the current state object, history, prefs, and model_manager ref.
        ConversationSnapshot already deep-copies mutable structures where needed.
        """
        snapshot = ConversationSnapshot(self.__dict__)
        logger.debug("[ConversationEngine] Snapshot created")
        return snapshot

    def restore_snapshot(self, snapshot):
        """
        Restore engine state from a given snapshot.
        This lets us roll back after a bad tool call, an unsafe model answer, etc.
        """
        self.__dict__ = snapshot.get_state()
        logger.debug("[ConversationEngine] State restored from snapshot")