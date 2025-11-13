# tests/state/test_clarifying_state.py

from metis.states.clarifying import ClarifyingState
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


def test_clarifying_transitions_to_executing():
    engine = _engine()
    engine.set_state(ClarifyingState())
    response = engine.respond("I meant the second option")

    assert "clarify" in response.lower()
    assert engine.state.__class__.__name__ == "ExecutingState"