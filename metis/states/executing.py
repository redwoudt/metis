# states/executing.py

from metis.states.base_state import ConversationState
from metis.states.summarizing import SummarizingState
from metis.services.prompt_service import render_prompt  # ✅ New import

class ExecutingState(ConversationState):
    """
    Executes the confirmed user task using available tools or logic.
    Transitions to SummarizingState after execution.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Build an execution-ready prompt, simulate execution, and move to summarization.

        :param engine: The conversation engine (context).
        :param user_input: The user's confirmed instruction.
        :return: A simulated response indicating task execution.
        """
        # Use new Builder + Template Method–based system to construct prompt
        prompt = render_prompt(
            prompt_type="executing",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        # Simulate execution (e.g., call tools, APIs, etc.)
        result = f"Executing task: {prompt}"

        # Transition to next state
        engine.set_state(SummarizingState())

        return result