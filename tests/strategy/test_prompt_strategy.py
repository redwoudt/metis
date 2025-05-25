from metis.strategy.default import DefaultPromptStrategy


def test_default_prompt_strategy():
    strategy = DefaultPromptStrategy()
    prompt = strategy.build_prompt({"user_id": "user_123"}, "hello")
    assert "DefaultPrompt" in prompt
