# tests/state/test_greeting_state.py

from metis.states.greeting import GreetingState
from metis.conversation_engine import ConversationEngine


def test_greeting_transitions_to_clarifying():
    """
    Ensures GreetingState responds with a friendly message and transitions to ClarifyingState.
    """
    engine = ConversationEngine()
    engine.set_state(GreetingState())

    user_input = "Hi"
    response = engine.respond(user_input)

    # Check for expected friendly tone or greeting intent
    assert any(keyword in response.lower() for keyword in ["assist", "welcome", "hello", "hi", "help"]), (
        f"Unexpected greeting response: {response}"
    )

    # Verify transition occurred
    assert engine.state.__class__.__name__ == "ClarifyingState"