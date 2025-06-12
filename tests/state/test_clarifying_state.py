# tests/state/test_clarifying_state.py

from metis.states.clarifying import ClarifyingState
from metis.conversation_engine import ConversationEngine

def test_clarifying_transitions_to_executing():
    engine = ConversationEngine()
    engine.set_state(ClarifyingState())
    response = engine.respond("I meant the second option")

    assert "clarify" in response
    assert engine.state.__class__.__name__ == "ExecutingState"