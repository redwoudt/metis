import pytest
from unittest.mock import MagicMock

from metis.states.greeting import GreetingState
from metis.states.executing import ExecutingState
from metis.states.summarizing import SummarizingState


class DummyEngine:
    def __init__(self):
        self.preferences = {
            "context": "System context",
            "tool_output": "Generated from tool",
            "tone": "Neutral",
            "persona": "Test Persona"
        }
        self.state_set = None
        self.model = None

    def set_state(self, new_state):
        self.state_set = new_state

    def respond(self, prompt):
        return f"[DUMMY RESPONSE] {prompt}"


# --- GreetingState ---
def test_greeting_state_responds_and_transitions():
    state = GreetingState()
    engine = DummyEngine()
    response = state.respond(engine, "Hi there")

    assert "hi" in response.lower() or "welcome" in response.lower()
    assert engine.state_set is not None


# --- ExecutingState ---
def test_executing_state_generates_execution_prompt():
    state = ExecutingState()
    engine = DummyEngine()
    response = state.respond(engine, "Deploy the app")

    assert "Executing task:" in response
    assert "Deploy the app" in response
    assert engine.state_set is not None


# --- SummarizingState ---
def test_summarizing_state_outputs_summary():
    state = SummarizingState()
    engine = DummyEngine()
    response = state.respond(engine, "Wrap it up")

    assert "Summary:" in response
    assert "Wrap it up" in response
    assert engine.state_set is not None