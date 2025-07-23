from metis.prompts.prompt import Prompt

def test_prompt_render_outputs_text():
    """Test that Prompt.render() produces a properly formatted string."""
    prompt = Prompt(
        task="Summarize the input clearly.",
        context="This conversation covers launch planning.",
        tool_output="Calendar shows 3 available windows.",
        tone="Supportive",
        persona="Concise Assistant",
        user_input="How should I schedule my week?"
    )
    result = prompt.render()
    assert isinstance(result, str)
    assert "Summarize the input clearly." in result
    assert "This conversation covers launch planning." in result
    assert "Calendar shows 3 available windows." in result
    assert "How should I schedule my week?" in result
    assert "[Tone: Supportive] [Persona: Concise Assistant]" in result

def test_prompt_with_missing_fields_renders_gracefully():
    """Prompt should still render even when some fields are omitted."""
    prompt = Prompt(
        task="Help the user decide.",
        context="",
        tool_output="",
        tone="",
        persona="",
        user_input="Should I use PostgreSQL or MongoDB?"
    )
    output = prompt.render()
    assert "Help the user decide." in output
    assert "Should I use PostgreSQL or MongoDB?" in output
    assert "[Tone:" not in output  # tone/persona skipped if not present
