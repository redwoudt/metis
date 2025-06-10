# tests/state/test_summarizing_state.py

from states.summarizing import SummarizingState
from conversation_engine import ConversationEngine

def test_summarizing_transitions_to_greeting():
    engine = ConversationEngine()
    engine.set_state(SummarizingState())
    response = engine.respond("Give me a summary")

    assert "Summary" in response
    assert engine.state.__class__.__name__ == "GreetingState"