# tests/state/test_greeting_state.py

from metis.states.greeting import GreetingState
from metis.states.clarifying import ClarifyingState
from metis.conversation_engine import ConversationEngine


# -------------------------------------------------------------------
# Dummy support classes for isolation
# -------------------------------------------------------------------

class DummyModelManager:
    """
    Simple fake model manager returning a fixed greeting narration.
    """
    def __init__(self, response="HELLO_THERE"):
        self.response = response

    def generate(self, prompt_text, **kwargs):
        return self.response


class DummyRequestHandler:
    """
    Minimal RequestHandler stub.

    Included so downstream states (e.g. ClarifyingState) can safely
    access engine.request_handler.config without raising errors.
    """
    config = {
        "tools": []
    }


class DummyEngine(ConversationEngine):
    """
    Minimal stub engine for GreetingState tests.
    """
    def __init__(self):
        self.preferences = {}
        self.user_id = "user_test"
        self.model_manager = DummyModelManager()
        self.request_handler = DummyRequestHandler()
        self.state = None

    def generate_with_model(self, prompt_text):
        return self.model_manager.generate(prompt_text)

    # Override to avoid ConversationEngine.on_enter hooks
    def set_state(self, new_state):
        self.state = new_state


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

def test_greeting_generates_friendly_output_and_transitions():
    """
    GreetingState should:
      1. Build a greeting prompt
      2. Produce model-generated narration
      3. Transition to ClarifyingState
    """
    engine = DummyEngine()
    engine.set_state(GreetingState())

    out = engine.state.respond(engine, "Hi there!")

    # 1. Returns the greeting narration
    assert out == "HELLO_THERE"

    # 2. Transition should occur
    assert isinstance(engine.state, ClarifyingState)


def test_greeting_responds_even_without_user_input():
    """
    GreetingState should handle empty input safely and still produce a greeting
    and transition to ClarifyingState.
    """
    engine = DummyEngine()
    engine.set_state(GreetingState())

    out = engine.state.respond(engine, "")

    assert out == "HELLO_THERE"
    assert isinstance(engine.state, ClarifyingState)


def test_greeting_does_not_modify_preferences():
    """
    GreetingState should not alter engine.preferences.
    """
    engine = DummyEngine()
    engine.preferences["foo"] = "bar"

    engine.set_state(GreetingState())
    _ = engine.state.respond(engine, "Hello!")

    assert engine.preferences["foo"] == "bar"
    assert isinstance(engine.state, ClarifyingState)