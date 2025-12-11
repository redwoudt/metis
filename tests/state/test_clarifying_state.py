# tests/state/test_clarifying_state.py

from metis.states.clarifying import ClarifyingState
from metis.states.executing import ExecutingState
from metis.conversation_engine import ConversationEngine


# -------------------------------------------------------------------
# Dummy engine + model for isolation
# -------------------------------------------------------------------

class DummyModelManager:
    """
    Minimal fake model manager that returns a preset response.
    """
    def __init__(self, response):
        self.response = response

    def generate(self, prompt_text, **kwargs):
        return self.response


class DummyEngine(ConversationEngine):
    """
    ConversationEngine stub that exposes:
    - preferences
    - fake model_manager
    - fake request_handler
    """
    def __init__(self, model_response):
        # A full ConversationEngine normally requires a ModelManager
        # so we set the internal model manager manually.
        self.model_manager = DummyModelManager(model_response)
        self.preferences = {}
        self.user_id = "u_test"
        self.request_handler = DummyRequestHandler()
        self.state = ClarifyingState()

    def generate_with_model(self, prompt_text):
        return self.model_manager.generate(prompt_text)

    # override state setter because real ConversationEngine tries to call on_enter()
    def set_state(self, new_state):
        self.state = new_state


class DummyRequestHandler:
    """
    RequestHandler stub — ClarifyingState does not execute tools,
    but it must reference handler in ExecutingState, so we stub one.
    """
    def execute_tool(self, tool_name, args, user, services):
        return "NOT_EXECUTED"


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

def test_clarifying_state_transitions_to_executing():
    """
    ClarifyingState should ALWAYS set the next state to ExecutingState after respond().
    The returned response comes from the model, not from the state machine itself.
    """
    engine = DummyEngine(model_response="CLARIFIED OUTPUT")

    out = engine.state.respond(engine, "I meant the second option")

    assert out == "CLARIFIED OUTPUT"
    assert isinstance(engine.state, ExecutingState)


def test_clarifying_extracts_tool_call():
    """
    If the model returns a structured tool_call dict, ClarifyingState must
    extract tool_name + tool_args and write them into engine.preferences.
    """
    model_response = {
        "tool_call": {
            "name": "search_web",
            "arguments": {"query": "riesling"}
        }
    }

    engine = DummyEngine(model_response=model_response)
    _ = engine.state.respond(engine, "Find wines")

    assert engine.preferences["tool_name"] == "search_web"
    assert engine.preferences["tool_args"]["query"] == "riesling"
    assert isinstance(engine.state, ExecutingState)


def test_clarifying_does_not_fail_without_tool_call():
    """
    If the model returns plain text, ClarifyingState should NOT crash or require tools.
    """
    engine = DummyEngine(model_response="No tool call here.")

    out = engine.state.respond(engine, "Just explain")

    assert out == "No tool call here."
    assert "tool_name" not in engine.preferences
    assert isinstance(engine.state, ExecutingState)