from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder
from metis.prompts.prompt import Prompt

# --- Default Prompt Builder Tests ---

def test_builds_complete_prompt():
    """
    Test that DefaultPromptBuilder correctly builds a full prompt with all fields.
    """
    builder = DefaultPromptBuilder()
    prompt = (
        builder
        .add_tone("Instructive", "Knowledge Guide")
        .add_task_instruction("Explain the core concept.")
        .add_context("We are discussing how transformers work.")
        .add_tool_output("Diagram and summary from Wiki retrieved.")
        .set_user_input("How does self-attention work?")
        .build()
    )
    output = prompt.render()
    assert "Explain the core concept." in output
    assert "transformers work" in output
    assert "Wiki retrieved" in output
    assert "self-attention" in output

def test_partial_prompt_works():
    """
    Test that prompt renders cleanly even if only task and input are given.
    """
    builder = DefaultPromptBuilder()
    prompt = (
        builder
        .add_task_instruction("Give a short answer.")
        .set_user_input("What is a neural network?")
        .build()
    )
    output = prompt.render()
    assert "Give a short answer." in output
    assert "What is a neural network?" in output

def test_prompt_is_instance_of_prompt():
    """
    Ensure that the builder returns a Prompt object.
    """
    builder = DefaultPromptBuilder()
    prompt = builder.set_user_input("Quick test").build()
    assert isinstance(prompt, Prompt)

def test_prompt_strips_whitespace():
    """
    Test that extra whitespace is stripped from each part of the prompt.
    """
    builder = DefaultPromptBuilder()
    prompt = (
        builder
        .add_tone("  Informal  ", "  Buddy  ")
        .add_task_instruction("\n   Summarize the article   \t")
        .add_context("    Context goes here     ")
        .add_tool_output("    Tool output...   ")
        .set_user_input("    Your input here   ")
        .build()
    )
    output = prompt.render()
    assert "Informal" in output
    assert "Buddy" in output
    assert "Summarize the article" in output
    assert "Context goes here" in output
    assert "Tool output..." in output
    assert "Your input here" in output