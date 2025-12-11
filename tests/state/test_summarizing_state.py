# tests/state/test_summarizing_state.py

from metis.states.summarizing import SummarizingState
from metis.states.greeting import GreetingState
from metis.conversation_engine import ConversationEngine


# -------------------------------------------------------------------
# Dummy support classes
# -------------------------------------------------------------------

class DummyModelManager:
    """
    Minimal fake model manager that returns a fixed string for summarization.
    """
    def __init__(self, response="SUMMARY_OUTPUT"):
        self.response = response

    def generate(self, prompt_text, **kwargs):
        return self.response


class DummyEngine(ConversationEngine):
    """
    A lightweight engine stub for SummarizingState tests.
    It must support:
      - preferences
      - model_manager
      - set_state
      - generate_with_model
    """

    def __init__(self):
        self.preferences = {}
        self.user_id = "tester"
        self.model_manager = DummyModelManager()
        self.state = None

    def generate_with_model(self, prompt_text):
        return self.model_manager.generate(prompt_text)

    # Override for simplicity (real engine also calls on_enter)
    def set_state(self, new_state):
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

    # Returned summary text
    assert output == "SUMMARY_OUTPUT"

    # State transition occurred
    assert isinstance(engine.state, GreetingState)


def test_summarizing_handles_empty_input_gracefully():
    """
    Even if the user provides an empty or irrelevant prompt,
    SummarizingState should still narrate and transition.
    """
    engine = DummyEngine()
    state = SummarizingState()

    output = state.respond(engine, "")

    assert output == "SUMMARY_OUTPUT"
    assert isinstance(engine.state, GreetingState)


def test_summarizing_does_not_modify_preferences_unnecessarily():
    """
    SummarizingState should not create or modify tool preferences.
    """
    engine = DummyEngine()
    engine.preferences["tool_output"] = "should not change"

    state = SummarizingState()
    state.respond(engine, "Summarize this")

    # Preferences should remain untouched
    assert engine.preferences["tool_output"] == "should not change"
    assert isinstance(engine.state, GreetingState)