def test_engine_generate_with_model_uses_strategy_when_present():
    from metis.conversation_engine import ConversationEngine

    class StubModelManager:
        def __init__(self):
            self.calls = []
        def generate(self, prompt: str, **kwargs):
            self.calls.append(("generate", prompt, kwargs))
            return "model-output"

    class StubStrategy:
        def __init__(self):
            self.calls = []
        def generate(self, model_manager, prompt: str, **kwargs):
            self.calls.append(("strategy-generate", prompt, dict(kwargs)))
            # strategy decides to call model_manager with modified kwargs
            kwargs.setdefault("max_tokens", 123)
            return model_manager.generate(prompt, **kwargs)

    mm = StubModelManager()
    engine = ConversationEngine(model_manager=mm)

    strategy = StubStrategy()
    engine.response_strategy = strategy

    out = engine.generate_with_model("hello", temperature=0.5)

    assert out == "model-output"
    assert strategy.calls == [("strategy-generate", "hello", {"temperature": 0.5})]
    # model manager should receive kwargs updated by strategy
    assert mm.calls == [("generate", "hello", {"temperature": 0.5, "max_tokens": 123})]


def test_engine_generate_with_model_falls_back_without_strategy():
    from metis.conversation_engine import ConversationEngine

    class StubModelManager:
        def __init__(self):
            self.calls = []
        def generate(self, prompt: str, **kwargs):
            self.calls.append((prompt, kwargs))
            return "ok"

    mm = StubModelManager()
    engine = ConversationEngine(model_manager=mm)

    engine.response_strategy = None
    out = engine.generate_with_model("hi", max_tokens=10)

    assert out == "ok"
    assert mm.calls == [("hi", {"max_tokens": 10})]