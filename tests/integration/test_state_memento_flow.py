# tests/integration/test_state_memento_flow.py

from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager

def test_state_memento_integration_flow():
    engine = ConversationEngine()
    memory = MemoryManager()

    # Initial greeting
    assert engine.state.__class__.__name__ == "GreetingState"
    engine.history.append("User: Start chat")

    # Save initial state
    snapshot = engine.create_snapshot()
    memory.save(snapshot)

    # Advance through states
    engine.respond("Hello")   # ClarifyingState
    engine.respond("Yes")     # ExecutingState
    engine.respond("Done")    # SummarizingState
    engine.respond("Thanks")  # ✅ triggers return to GreetingState

    assert engine.state.__class__.__name__ == "GreetingState"
    assert len(engine.history) == 5  # 1 manual, 4 from state responses

    # Roll back to original snapshot
    engine.restore_snapshot(memory.restore_last())

    assert engine.state.__class__.__name__ == "GreetingState"
    assert engine.history == ["User: Start chat"]