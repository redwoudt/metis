# tests/state/test_state_prompt_integration.py
#
# Integration-ish tests for the state objects using a tiny in-memory Engine stub.
# These tests intentionally avoid the old `engine.request_handler` API and instead
# exercise a minimal Engine surface: `generate_with_model(...)`, `execute_tool(...)`,
# `set_state(...)`, and a shared `preferences` dict.

import logging

from metis.states.greeting import GreetingState
from metis.states.clarifying import ClarifyingState
from metis.states.executing import ExecutingState
from metis.states.summarizing import SummarizingState


logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Dummy Support Classes
# -------------------------------------------------------------------

class DummyModelManager:
    """Minimal fake model manager returning predictable text."""

    def __init__(self, response: str = "MODEL_RESPONSE"):
        self.response = response

    def generate(self, prompt_text: str, **kwargs) -> str:
        return self.response


class DummyToolExecutor:
    """Fake tool executor to verify call behavior."""

    def __init__(self):
        self.calls = []

    def execute_tool(self, tool_name: str, args: dict, user):
        self.calls.append((tool_name, args, user))
        return f"RESULT:{tool_name}:{args}"


class DummyEngine:
    """
    Minimal engine supporting the methods used by the state classes.
    State classes should treat this as the system façade.
    """

    def __init__(self, model_response: str = "MODEL_RESPONSE"):
        self.preferences = {}
        self.user_id = "tester"
        self.model_manager = DummyModelManager(model_response)
        self.tool_executor = DummyToolExecutor()
        self.state = None

    def generate_with_model(self, prompt_text: str) -> str:
        return self.model_manager.generate(prompt_text)

    def execute_tool(self, tool_name: str, args: dict, user):
        return self.tool_executor.execute_tool(tool_name, args, user)

    def set_state(self, new_state) -> None:
        self.state = new_state


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

def test_greeting_state_generates_narration_and_transitions():
    engine = DummyEngine("HELLO!")
    engine.state = GreetingState()

    out = engine.state.respond(engine, "Hi there")

    assert out == "HELLO!"
    assert isinstance(engine.state, ClarifyingState)


def test_executing_state_runs_tool_and_transitions():
    engine = DummyEngine("EXECUTION_NARRATION")

    # Preconfigure preferences to simulate tool selection.
    engine.preferences["tool_name"] = "search_web"
    engine.preferences["tool_args"] = {"query": "malbec"}

    engine.state = ExecutingState()
    out = engine.state.respond(engine, "Run search")

    # Model narration is returned.
    assert out == "Executing: EXECUTION_NARRATION"

    # Tool executed and stored into preferences.
    assert engine.preferences["tool_output"] == "RESULT:search_web:{'query': 'malbec'}"
    assert engine.tool_executor.calls == [
        ("search_web", {"query": "malbec"}, "tester")
    ]

    # Transition occurred.
    assert isinstance(engine.state, SummarizingState)


def test_executing_state_handles_no_tool_safely():
    engine = DummyEngine("NO_TOOL_NARRATION")
    engine.state = ExecutingState()

    out = engine.state.respond(engine, "Nothing to run")

    assert out == "Executing: NO_TOOL_NARRATION"
    assert "tool_output" not in engine.preferences
    assert isinstance(engine.state, SummarizingState)


def test_summarizing_state_generates_summary_and_transitions():
    engine = DummyEngine("SUMMARY_TEXT")
    engine.state = SummarizingState()

    out = engine.state.respond(engine, "Wrap up")

    assert out == "Summary: SUMMARY_TEXT"
    assert isinstance(engine.state, GreetingState)


def test_summarizing_state_does_not_change_preferences():
    engine = DummyEngine("SUMMARY")
    engine.preferences["keep"] = "value"

    engine.state = SummarizingState()
    engine.state.respond(engine, "summarize")

    assert engine.preferences["keep"] == "value"
    assert isinstance(engine.state, GreetingState)