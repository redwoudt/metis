# states/executing.py

from metis.states.base_state import ConversationState
from metis.states.summarizing import SummarizingState
from metis.prompts.prompt_builder import PromptBuilder

class ExecutingState(ConversationState):
    """
    Executes the confirmed user task using available tools or logic.
    Transitions to SummarizingState after execution.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def respond(self, engine, user_input):
        """
        Build an execution-ready prompt, simulate execution, and move to summarization.

        :param engine: The conversation engine (context).
        :param user_input: The user's confirmed instruction.
        :return: A simulated response indicating task execution.
        """
        # Generate a task-specific prompt
        state_name = self.__class__.__name__
        prompt = self.prompt_builder.build_prompt(state_name, user_input, engine.preferences)

        # Simulate execution (in a real system this could trigger tools or external calls)
        result = f"Executing task: {prompt}"

        # Transition to next state
        engine.set_state(SummarizingState())

        return result