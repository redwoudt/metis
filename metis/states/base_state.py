# states/base_state.py

from abc import ABC, abstractmethod

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
    def respond(self, engine, user_input):
        """
        Handle user input and return a response.
        May trigger state transitions via engine.set_state().

        :param engine: The ConversationEngine context.
        :param user_input: The latest user input string.
        :return: A response string from the assistant.
        """
        pass