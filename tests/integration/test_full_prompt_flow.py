from metis.services.prompt_service import render_prompt
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

# --- Full system integration test for rendering and response ---

def test_full_prompt_flow_generates_response():
    """Simulates full prompt flow from render to engine.respond."""
    engine = _engine()

    prompt = render_prompt(
        prompt_type="summarize",
        user_input="Please summarize our discussion about onboarding.",
        context="We talked about onboarding new developers to the platform.",
        tool_output="Checklist already generated.",
        tone="Supportive",
        persona="Technical Mentor"
    )

    response = engine.respond(prompt)

    assert isinstance(response, str)
    assert "summarize" in response.lower() or "onboarding" in response.lower()


def test_full_prompt_flow_handles_empty_context():
    """Ensures full prompt flow works when some optional fields are omitted."""
    engine = _engine()

    prompt = render_prompt(
        prompt_type="plan",
        user_input="How should I prioritize my week?",
        context="",
        tool_output="",
        tone="Organized",
        persona="Coach"
    )

    response = engine.respond(prompt)

    assert isinstance(response, str)
    assert "prioritize" in response.lower() or "plan" in response.lower()