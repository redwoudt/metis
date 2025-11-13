# tests/integration/test_state_memento_flow.py

from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager
from metis.memory.manager import MemoryManager


def _engine(vendor: str = "mock", model: str = "stub") -> ConversationEngine:
    """Helper to build an engine wired through the Bridge (ModelManager)."""
    client = ModelFactory.for_role(
        "analysis",
        {"vendor": vendor, "model": model, "policies": {}},
    )
    return ConversationEngine(model_manager=ModelManager(client))


def test_state_memento_integration_flow():
    engine = _engine()
    memory = MemoryManager()

    # Initial greeting
    assert engine.state.__class__.__name__ == "GreetingState"
    engine.history.append("User: Start chat")

    # Save initial state (snapshot must capture the current state + history + model_manager)
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