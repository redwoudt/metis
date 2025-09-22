# states/clarifying.py

from metis.states.base_state import ConversationState
from metis.states.executing import ExecutingState


class ClarifyingState(ConversationState):
    """
    A state that confirms or refines the user's intent before taking action.
    Transitions to ExecutingState once clarification is complete.
    """
    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Generate a clarification prompt and transition to ExecutingState.

        :param engine: The conversation engine (context).
        :param user_input: The user's clarification input.
        :return: A follow-up message seeking confirmation or moving to execution.
        """
        # Logic could involve NLU, confidence scoring, or follow-up validation in a real system.
        clarification_prompt = f"Just to clarify: did you mean '{user_input}'?"

        # Transition to the next state
        engine.set_state(ExecutingState())

        return clarification_prompt