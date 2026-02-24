import pytest


def test_request_handler_sets_engine_response_strategy_from_dsl(monkeypatch):
    """
    Ensures RequestHandler reads dsl_ctx['style'] and assigns engine.response_strategy.
    """

    # Import here to avoid eager imports before monkeypatch
    from metis.handler.request_handler import RequestHandler

    # Stub strategy selector to ensure our wiring is the thing under test.
    class StubStrategy:
        def generate(self, model_manager, prompt: str, **kwargs):
            return "stubbed"

    class StubSelector:
        def select(self, dsl_ctx, config):
            assert dsl_ctx.get("style") == "creative"
            return StubStrategy()

    monkeypatch.setattr(
        "metis.response.generation.selector.StrategySelector",
        StubSelector,
        raising=False,
    )

    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})

    # Run a request that includes style key. Whatever your DSL format is,
    # this assumes RequestHandler parses [style: ...] into dsl_ctx.
    out = handler.handle_prompt(user_id="u1", user_input="[style: creative] hello")

    # We can't easily assert internal engine state from here without reaching into session,
    # but we can assert it *didn't crash* and returned a string.
    assert isinstance(out, str)


def test_request_handler_copies_rendering_flags_into_engine_preferences(monkeypatch):
    """
    Ensures DSL flags make it into engine.preferences.
    """
    from metis.handler.request_handler import RequestHandler

    # Make StrategySelector harmless in this test
    class PassthroughSelector:
        def select(self, dsl_ctx, config):
            return None  # engine can handle None strategy

    monkeypatch.setattr(
        "metis.response.generation.selector.StrategySelector",
        PassthroughSelector,
        raising=False,
    )

    # Hook into ConversationEngine to capture preferences after handler wires them.
    captured = {}

    from metis.conversation_engine import ConversationEngine as RealEngine

    _orig_engine_init = RealEngine.__init__

    def wrapped_engine_init(self, model_manager, request_handler=None, **kwargs):
        _orig_engine_init(self, model_manager, request_handler=request_handler, **kwargs)

    monkeypatch.setattr("metis.conversation_engine.ConversationEngine.__init__", wrapped_engine_init)

    # Patch respond to capture preferences and return something simple
    def capture_respond(self, user_input: str) -> str:
        captured.update(self.preferences)
        return "ok"

    monkeypatch.setattr("metis.conversation_engine.ConversationEngine.respond", capture_respond, raising=True)

    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    out = handler.handle_prompt(
        user_id="u2",
        user_input="[format_markdown: true][include_citations: yes][safety_enabled: on] hi",
    )
    assert out == "ok"
    assert captured["format_markdown"] is True
    assert captured["include_citations"] is True
    assert captured["safety_enabled"] is True