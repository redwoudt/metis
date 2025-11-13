# tests/state/test_executing_state.py

from metis.states.executing import ExecutingState
from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager


def _engine(vendor: str = "mock", model: str = "stub") -> ConversationEngine:
    """Helper to build an engine wired through the Bridge (ModelManager)."""
    client = ModelFactory.for_role(
        "analysis",
        {"vendor": vendor, "model": model, "policies": {}},
    )
    return ConversationEngine(model_manager=ModelManager(client))


def test_executing_transitions_to_summarizing():
    engine = _engine()
    engine.set_state(ExecutingState())
    response = engine.respond("Run report")

    assert "execut" in response.lower() or "running" in response.lower()
    assert engine.state.__class__.__name__ == "SummarizingState"