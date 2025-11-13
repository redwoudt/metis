# tests/state/test_greeting_state.py

from metis.states.greeting import GreetingState
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


def test_greeting_transitions_to_clarifying():
    """
    Ensures GreetingState responds with a friendly message and transitions to ClarifyingState.
    """
    engine = _engine()
    engine.set_state(GreetingState())

    user_input = "Hi"
    response = engine.respond(user_input)

    # Check for expected friendly tone or greeting intent
    assert any(keyword in response.lower() for keyword in ["assist", "welcome", "hello", "hi", "help"]), (
        f"Unexpected greeting response: {response}"
    )

    # Verify transition occurred
    assert engine.state.__class__.__name__ == "ClarifyingState"