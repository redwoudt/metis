from metis.states.greeting import GreetingState  # Import initial conversation state
from metis.memory.snapshot import ConversationSnapshot  # Import Memento class for state snapshots
import copy  # Used indirectly via ConversationSnapshot for deep copying

class ConversationEngine:
    """
    Acts as the Originator in the Memento pattern and as the context in the State pattern.
    Manages conversation state transitions and supports memory snapshot/restore.
    """
    def __init__(self):
        self.state = GreetingState()  # Set initial state to Greeting
        self.history = []  # Tracks the conversation log
        self.preferences = {"tone": "friendly"}  # Stores user preferences

    def set_state(self, new_state):
        """
        Transition to a new conversation state.
        """
        self.state = new_state

    def respond(self, user_input):
        """
        Delegate response logic to the current state.
        Append the response to conversation history.
        """
        response = self.state.respond(self, user_input)
        self.history.append(response)
        return response

    def create_snapshot(self):
        """
        Create a deep snapshot of the engine's current internal state.
        Used for rollback or checkpointing.
        """
        return ConversationSnapshot(self.__dict__)

    def restore_snapshot(self, snapshot):
        """
        Restore engine state from a given snapshot.
        Overwrites current internal state safely.
        """
        self.__dict__ = snapshot.get_state()