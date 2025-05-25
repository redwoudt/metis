from metis.components.prompt_builder import PromptBuilder


def test_prompt_builder():
    builder = PromptBuilder()
    session = {"user_id": "user_123"}
    prompt = builder.build(session, "Generate summary")
    assert "user_123" in prompt
