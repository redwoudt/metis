import pytest
from metis.prompts.prompt import Prompt

# Core templates
from metis.prompts.templates.summarization_prompt import SummarizationPrompt
from metis.prompts.templates.planning_prompt import PlanningPrompt
from metis.prompts.templates.critique_prompt import CritiquePrompt
from metis.prompts.templates.clarifying_prompt import ClarifyingPrompt

# Conditional imports (may not exist yet)
try:
    from metis.prompts.templates.greeting_prompt import GreetingPrompt
except ImportError:
    GreetingPrompt = None

try:
    from metis.prompts.templates.executing_prompt import ExecutingPrompt
except ImportError:
    ExecutingPrompt = None


# --- SummarizationPrompt ---
def test_summarization_prompt_builds_cleanly():
    """
    Test that SummarizationPrompt builds a structured prompt
    with a summarization task and context.
    """
    template = SummarizationPrompt(context="We discussed launch plans.")
    prompt = template.build_prompt("Please summarize.")
    assert isinstance(prompt, Prompt)
    assert "Summarize the conversation clearly and briefly." in prompt.render()
    assert "We discussed launch plans." in prompt.render()
    assert "Please summarize." in prompt.render()


# --- PlanningPrompt ---
def test_planning_prompt_includes_tool_output():
    """
    Test that PlanningPrompt correctly embeds planning instruction,
    context, and tool output into the final rendered prompt.
    """
    template = PlanningPrompt(
        context="Schedule for next week",
        tool_output="Calendar: 5 free slots",
        tone="Supportive",
        persona="Time Coach"
    )
    prompt = template.build_prompt("Plan my week.")
    rendered = prompt.render()
    assert "step-by-step plan" in rendered
    assert "Schedule for next week" in rendered
    assert "Calendar: 5 free slots" in rendered
    assert "Plan my week." in rendered


# --- ClarifyingPrompt ---
def test_clarifying_prompt_suggests_questions():
    """
    Test that ClarifyingPrompt builds a prompt that requests clarification.
    """
    template = ClarifyingPrompt(
        context="Ambiguous request",
        tone="Inquisitive",
        persona="Curious Assistant"
    )
    prompt = template.build_prompt("Make it better.")
    output = prompt.render()
    assert "clarifying questions" in output.lower()
    assert "Ambiguous request" in output
    assert "Make it better." in output


# --- CritiquePrompt ---
def test_critique_prompt_evaluates_content():
    """
    Test that CritiquePrompt constructs a prompt for constructive feedback.
    """
    template = CritiquePrompt(
        context="Draft blog post",
        tool_output="Readability: 60, Tone: informal",
        tone="Analytical",
        persona="Content Reviewer"
    )
    prompt = template.build_prompt("Evaluate this post.")
    result = prompt.render()
    assert "constructive feedback" in result
    assert "Draft blog post" in result
    assert "Evaluate this post." in result


# --- Optional: GreetingPrompt ---
@pytest.mark.skipif(GreetingPrompt is None, reason="GreetingPrompt not implemented")
def test_greeting_prompt_outputs_welcome():
    """
    If implemented, tests that GreetingPrompt builds a welcoming message.
    """
    template = GreetingPrompt(
        context="First-time user",
        tone="Friendly",
        persona="Warm Greeter"
    )
    prompt = template.build_prompt("Hi there!")
    output = prompt.render()
    assert "hi" in output.lower() or "welcome" in output.lower()


# --- Optional: ExecutingPrompt ---
@pytest.mark.skipif(ExecutingPrompt is None, reason="ExecutingPrompt not implemented")
def test_executing_prompt_runs_task():
    """
    If implemented, tests that ExecutingPrompt builds a command-execution prompt.
    """
    template = ExecutingPrompt(
        context="Production deployment",
        tool_output="Script deployed successfully",
        tone="Neutral",
        persona="Automation Agent"
    )
    prompt = template.build_prompt("Deploy the latest version.")
    output = prompt.render()
    assert "Deploy the latest version." in output
    assert "Script deployed successfully" in output
    assert "execute" in output.lower()