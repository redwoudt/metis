# tests/state/test_executing_state.py

from states.executing import ExecutingState
from conversation_engine import ConversationEngine

def test_executing_transitions_to_summarizing():
    engine = ConversationEngine()
    engine.set_state(ExecutingState())
    response = engine.respond("Run report")

    assert "Executing task" in response
    assert engine.state.__class__.__name__ == "SummarizingState"