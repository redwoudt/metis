def test_engine_response_post_processing_is_off_by_default(monkeypatch):
    from metis.conversation_engine import ConversationEngine

    class StubModelManager:
        def generate(self, prompt: str, **kwargs):
            return "ignored"

    engine = ConversationEngine(model_manager=StubModelManager())

    # Force a simple state response without running your real state machine:
    class StubState:
        next_state = None
        def respond(self, engine, user_input: str) -> str:
            return "raw"

    engine.state = StubState()

    out = engine.respond("hi")
    assert out == "raw"


def test_engine_response_post_processing_applies_when_flags_enabled(monkeypatch):
    from metis.conversation_engine import ConversationEngine

    class StubModelManager:
        def generate(self, prompt: str, **kwargs):
            return "ignored"

    engine = ConversationEngine(model_manager=StubModelManager())

    class StubState:
        next_state = None
        def respond(self, engine, user_input: str) -> str:
            return "raw"

    engine.state = StubState()

    # Enable formatting/citations; SafetyDecorator may be no-op (that’s fine).
    engine.preferences["format_markdown"] = True
    engine.preferences["include_citations"] = True

    out = engine.respond("hi")

    # These assertions assume your FormattingDecorator and CitationDecorator behave as designed.
    assert out.startswith("## Response")
    assert "Sources:" in out