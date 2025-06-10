# states/greeting.py

from states.base_state import ConversationState
from states.clarifying import ClarifyingState
from prompts.prompt_builder import PromptBuilder

class GreetingState(ConversationState):
    """
    The initial state of the conversation.
    Greets the user and transitions to ClarifyingState.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def respond(self, engine, user_input):
        """
        Respond with a greeting and move to ClarifyingState.

        :param engine: The conversation engine (context).
        :param user_input: The initial user message.
        :return: A welcome message.
        """
        state_name = self.__class__.__name__
        prompt = self.prompt_builder.build_prompt(state_name, user_input, engine.preferences)

        # Transition to next state
        engine.set_state(ClarifyingState())

        return f"{prompt}"