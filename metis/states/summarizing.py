# states/summarizing.py

from metis.states.base_state import ConversationState
from metis.services.prompt_service import render_prompt  # ✅ New import

class SummarizingState(ConversationState):
    """
    Summarizes the recent interaction or outcome.
    Resets the flow back to GreetingState for a new turn.
    """

    def respond(self, engine, user_input):
        """
        Provide a summary and loop back to GreetingState.

        :param engine: The conversation engine (context).
        :param user_input: Optional input triggering summary.
        :return: Summary message.
        """
        from metis.states.greeting import GreetingState  # ✅ Local import to avoid circular dependency

        # Use the new Builder + Template Method–based prompt rendering
        prompt = render_prompt(
            prompt_type="summarize",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        engine.set_state(GreetingState())
        return f"Summary: {prompt}"