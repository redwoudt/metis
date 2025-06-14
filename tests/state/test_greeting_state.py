# tests/state/test_greeting_state.py

from metis.states.greeting import GreetingState
from metis.conversation_engine import ConversationEngine

def test_greeting_transitions_to_clarifying():
    engine = ConversationEngine()
    engine.set_state(GreetingState())
    response = engine.respond("Hi")

    assert "assist" in response or "Welcome" in response
    assert engine.state.__class__.__name__ == "ClarifyingState"