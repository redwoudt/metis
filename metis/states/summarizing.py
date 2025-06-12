# states/summarizing.py

from metis.states.base_state import ConversationState
from metis.prompts.prompt_builder import PromptBuilder

class SummarizingState(ConversationState):
    """
    Summarizes the recent interaction or outcome.
    Resets the flow back to GreetingState for a new turn.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def respond(self, engine, user_input):
        """
        Provide a summary and loop back to GreetingState.

        :param engine: The conversation engine (context).
        :param user_input: Optional input triggering summary.
        :return: Summary message.
        """
        from metis.states.greeting import GreetingState  # ✅ Local import to avoid circular dependency

        state_name = self.__class__.__name__
        prompt = self.prompt_builder.build_prompt(state_name, user_input, engine.preferences)

        engine.set_state(GreetingState())
        return f"Summary: {prompt}"