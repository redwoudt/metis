from metis.states.greeting import GreetingState  # Import initial conversation state
from metis.memory.snapshot import ConversationSnapshot  # Import Memento class for state snapshots
import copy  # Used indirectly via ConversationSnapshot for deep copying
import logging

logger = logging.getLogger(__name__)

class ConversationEngine:
    """
    Acts as the Originator in the Memento pattern and as the context in the State pattern.
    Manages conversation state transitions and supports memory snapshot/restore.
    """
    def __init__(self):

        self.state = GreetingState()  # Set initial state to Greeting
        self.history = []  # Tracks the conversation log
        self.preferences = {"tone": "friendly"}  # Stores user preferences
        self.model = None
        logger.debug("[ConversationEngine] Initialized with GreetingState, empty history, and preferences=%s", self.preferences)

    def set_state(self, new_state):
        """
        Transition to a new conversation state.
        """
        logger.debug("[ConversationEngine] Transitioning to new state: %s", new_state.__class__.__name__)
        self.state = new_state

    def respond(self, user_input):
        """
        Delegate response logic to the current state.
        Append the response to conversation history.
        """
        logger.debug("[ConversationEngine] Calling respond on state: %s with user_input='%s'", self.state.__class__.__name__, user_input)
        response = self.state.respond(self, user_input)
        self.history.append(response)
        logger.debug("[ConversationEngine] Response appended to history. Total entries: %d", len(self.history))
        return response

    def create_snapshot(self):
        """
        Create a deep snapshot of the engine's current internal state.
        Used for rollback or checkpointing.
        """
        snapshot = ConversationSnapshot(self.__dict__)
        logger.debug("[ConversationEngine] Snapshot created")
        return snapshot

    def restore_snapshot(self, snapshot):
        """
        Restore engine state from a given snapshot.
        Overwrites current internal state safely.
        """
        self.__dict__ = snapshot.get_state()
        logger.debug("[ConversationEngine] State restored from snapshot")

    def get_model(self):
        """
        Return the underlying model instance if it was injected by the current state.
        Useful for testing and debugging.
        """
        logger.debug("[ConversationEngine] Returning model: %s", type(self.model).__name__ if self.model else None)
        return self.model

    def set_model(self, model):
        """
        Injects the model into the engine for later reference.
        This enables the current conversation state to access the model during response generation.
        """
        self.model = model
        logger.debug("[ConversationEngine] Model set: %s", type(model).__name__)