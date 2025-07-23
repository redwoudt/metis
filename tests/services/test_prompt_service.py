import pytest
from metis.services.prompt_service import generate_prompt, render_prompt, PromptFormatter
from metis.prompts.prompt import Prompt

# --- Generate Prompt Tests ---

def test_generate_prompt_returns_prompt():
    """Test that generate_prompt returns a Prompt instance."""
    prompt = generate_prompt(
        prompt_type="summarize",
        user_input="Summarize this",
        context="Chat log",
        tool_output="N/A",
        tone="Neutral",
        persona="Summarizer"
    )
    assert isinstance(prompt, Prompt)
    assert "Summarize this" in prompt.user_input


def test_render_prompt_returns_string():
    """Test that render_prompt returns a formatted string."""
    result = render_prompt(
        prompt_type="plan",
        user_input="Help me plan my day",
        context="Today is Monday",
        tool_output="Calendar shows 4 open slots",
        tone="Organized",
        persona="Planner"
    )
    assert isinstance(result, str)
    assert "Help me plan my day" in result
    assert "Calendar shows" in result


def test_generate_prompt_invalid_type():
    """Test that passing an unknown prompt_type raises ValueError."""
    with pytest.raises(ValueError):
        generate_prompt("unknown", "Test input")


# --- Prompt Formatter Utility Tests ---

def test_formatter_truncates_long_context():
    """Ensure long context is truncated safely."""
    long_text = "A" * 5000
    prompt = Prompt(task="t", context=long_text, tool_output="", tone="", persona="", user_input="u")
    truncated = PromptFormatter.truncate(prompt, max_tokens=1000)
    assert len(truncated.context) <= 500


def test_formatter_strips_whitespace():
    """Test that PromptFormatter removes leading/trailing whitespace."""
    prompt = Prompt(
        task="   Do something   ",
        context="   Context here   ",
        tool_output="   Output here   ",
        tone="  Neutral  ",
        persona="  Assistant  ",
        user_input="   User input   "
    )
    cleaned = PromptFormatter.normalize_whitespace(prompt)
    assert cleaned.task == "Do something"
    assert cleaned.context == "Context here"
    assert cleaned.tool_output == "Output here"
    assert cleaned.user_input == "User input"