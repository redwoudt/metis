# states/greeting.py

from metis.states.base_state import ConversationState
from metis.states.clarifying import ClarifyingState
from metis.services.prompt_service import render_prompt  # ✅ New import

class GreetingState(ConversationState):
    """
    The initial state of the conversation.
    Greets the user and transitions to ClarifyingState.
    """

    def respond(self, engine, user_input):
        """
        Respond with a greeting and move to ClarifyingState.

        :param engine: The conversation engine (context).
        :param user_input: The initial user message.
        :return: A welcome message.
        """
        # Use the new Builder + Template Method–based prompt construction
        prompt = render_prompt(
            prompt_type="greeting",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        # Transition to next state
        engine.set_state(ClarifyingState())

        return f"{prompt}"