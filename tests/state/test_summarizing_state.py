# tests/state/test_summarizing_state.py

"""
SummarizingState unit tests.

These tests intentionally use a lightweight "engine" stub instead of the full
ConversationEngine. The only contract we care about here is what
SummarizingState calls:
  - engine.preferences (dict)
  - engine.user_id (str)
  - engine.model_manager.generate(...)
  - engine.generate_with_model(prompt_text)
  - engine.set_state(new_state)

If the real engine API evolves, these tests should remain stable as long as
SummarizingState's expectations remain the same.
"""

from metis.states.summarizing import SummarizingState
from metis.states.greeting import GreetingState


# -------------------------------------------------------------------
# Dummy support classes
# -------------------------------------------------------------------

class DummyModelManager:
    """Minimal fake model manager that returns a fixed string for summarization."""
    def __init__(self, response: str = "SUMMARY_OUTPUT"):
        self.response = response

    def generate(self, prompt_text: str, **kwargs) -> str:
        return self.response


class DummyEngine:
    """
    A lightweight engine stub for SummarizingState tests.
    Mirrors only the attributes/methods SummarizingState relies on.
    """

    def __init__(self):
        self.preferences = {}
        self.user_id = "user_test"
        self.model_manager = DummyModelManager()
        self.state = None

    def generate_with_model(self, prompt_text: str) -> str:
        # In the real engine, this may delegate to a model manager / model selector.
        return self.model_manager.generate(prompt_text)

    def set_state(self, new_state) -> None:
        # Keep it simple: just set the state.
        self.state = new_state


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

def test_summarizing_generates_narration_and_transitions():
    """
    SummarizingState should:
      1. Build summarization prompt
      2. Generate narration from the model
      3. Transition back to GreetingState
    """
    engine = DummyEngine()
    state = SummarizingState()

    output = state.respond(engine, "Please summarize the conversation")

    # Post-refactor behavior: return raw model output (no "Summary: " prefix)
    assert output == "Summary: SUMMARY_OUTPUT"

    # State transition occurred
    assert isinstance(engine.state, GreetingState)


def test_summarizing_handles_empty_input_gracefully():
    """
    Even if the user provides an empty prompt, SummarizingState should still
    generate narration and transition.
    """
    engine = DummyEngine()
    state = SummarizingState()

    output = state.respond(engine, "")

    assert output == "Summary: SUMMARY_OUTPUT"
    assert isinstance(engine.state, GreetingState)


def test_summarizing_does_not_modify_preferences_unnecessarily():
    """SummarizingState should not create or modify tool preferences."""
    engine = DummyEngine()
    engine.preferences["tool_output"] = "should not change"

    state = SummarizingState()
    state.respond(engine, "Summarize this")

    # Preferences should remain untouched
    assert engine.preferences["tool_output"] == "should not change"
    assert isinstance(engine.state, GreetingState)