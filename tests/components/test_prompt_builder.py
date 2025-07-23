"""
Tests for PromptBuilder, including default and JSON formatting, sanitization, and templates.
"""

# --- Imports ---
from metis.components.prompt_builder import PromptBuilder
from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder
from metis.prompts.templates.summarization_prompt import SummarizationPrompt
from metis.prompts.templates.critique_prompt import CritiquePrompt


# --- Legacy PromptBuilder Tests ---

def test_prompt_builder_default():
    # Tests default prompt formatting using the original PromptBuilder class
    builder = PromptBuilder()
    session = {"user_id": "user_123", "history": []}
    result = builder.build(session, "Summarize this text")
    assert "Summarize the following input" in result


def test_prompt_builder_json():
    # Tests JSON format option in the original PromptBuilder
    builder = PromptBuilder(format_style="json")
    session = {"user_id": "user_json", "history": [("Hi", "Hello")]}
    result = builder.build(session, "Plan my day")
    assert '"session": "user_json"' in result
    assert "Plan my day" in result


def test_prompt_sanitization():
    # Tests sanitization of unsafe or poorly formatted user input
    builder = PromptBuilder()
    session = {"user_id": "user_123", "history": []}
    dirty_input = "<script>alert('hi')</script>    Please plan   this"
    result = builder.build(session, dirty_input)
    assert "&lt;script&gt;alert(&#x27;hi&#x27;)&lt;/script&gt;" in result
    assert "Please plan this" in result


# --- New Builder + Template Method Tests ---

def test_default_prompt_builder_output():
    # Tests step-by-step construction of a Prompt using DefaultPromptBuilder
    builder = DefaultPromptBuilder()
    prompt = (
        builder
        .add_tone("Neutral", "Concise Assistant")
        .add_task_instruction("Summarize this")
        .add_context("Conversation about travel")
        .add_tool_output("")
        .set_user_input("Where should I go?")
        .build()
    )
    result = prompt.render()
    assert "Summarize this" in result
    assert "Where should I go?" in result
    assert "[Tone: Neutral" in result


def test_summarization_prompt_template():
    # Tests the SummarizationPrompt class using the Template Method pattern
    template = SummarizationPrompt(context="Discussed trip planning.")
    prompt = template.build_prompt("Summarize this chat.")
    output = prompt.render()
    assert "Summarize the conversation clearly and briefly." in output
    assert "Discussed trip planning." in output
    assert "Summarize this chat." in output


def test_critique_prompt_template():
    # Tests the CritiquePrompt class with context and tool output included
    template = CritiquePrompt(
        context="Startup pitch: AI tool for lawyers.",
        tool_output="Feedback: promising but crowded space.",
        tone="Analytical",
        persona="Critical Reviewer"
    )
    prompt = template.build_prompt("Evaluate this idea.")
    output = prompt.render()
    assert "Critique the content with constructive feedback" in output
    assert "Startup pitch: AI tool for lawyers." in output
    assert "Evaluate this idea." in output