# states/base_state.py

from abc import ABC, abstractmethod

class ConversationState(ABC):
    """
    Abstract base class for all conversation states.
    Defines the interface that each concrete state must implement.
    """

    @abstractmethod
    def respond(self, engine, user_input):
        """
        Handle user input and return a response.
        May trigger state transitions via engine.set_state().

        :param engine: The ConversationEngine context.
        :param user_input: The latest user input string.
        :return: A response string from the assistant.
        """
        pass