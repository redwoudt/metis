# tests/state/test_summarizing_state.py

from metis.states.summarizing import SummarizingState
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


def test_summarizing_transitions_to_greeting():
    engine = _engine()
    engine.set_state(SummarizingState())
    response = engine.respond("Give me a summary")

    assert "summary" in response.lower()
    assert engine.state.__class__.__name__ == "GreetingState"