# tests/state/test_executing_state.py

from metis.states.executing import ExecutingState
from metis.states.summarizing import SummarizingState
from metis.conversation_engine import ConversationEngine


# -------------------------------------------------------------------
# Dummy support classes
# -------------------------------------------------------------------

class DummyModelManager:
    """
    Simple fake model manager returning a fixed string for narration.
    """
    def __init__(self, response="MODEL_NARRATION"):
        self.response = response

    def generate(self, prompt_text, **kwargs):
        return self.response


class DummyHandler:
    """
    Simulates RequestHandler.execute_tool().

    We also provide a minimal `config` attribute to match the
    refactored RequestHandler contract.
    """
    def __init__(self):
        self.calls = []
        self.config = {
            "tools": []  # present for consistency with ClarifyingState
        }

    def execute_tool(self, tool_name, args, user, services):
        self.calls.append((tool_name, args, user))
        return f"RESULT:{tool_name}:{args}"


class DummyEngine(ConversationEngine):
    """
    Minimal engine for ExecutingState testing:
    - Has preferences
    - Has user_id
    - Has model_manager
    - Has request_handler (with config)
    """

    def __init__(self):
        self.preferences = {}
        self.user_id = "tester"
        self.request_handler = DummyHandler()
        self.model_manager = DummyModelManager()
        self.state = None

    def generate_with_model(self, prompt_text):
        return self.model_manager.generate(prompt_text)

    # Override to avoid ConversationEngine on_enter hooks
    def set_state(self, new_state):
        self.state = new_state


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

def test_executing_runs_tool_generates_narration_and_transitions():
    """
    ExecutingState should:
    1. Run the selected tool through request_handler.execute_tool
    2. Store tool_output in engine.preferences
    3. Generate narration via model
    4. Transition to SummarizingState
    """
    engine = DummyEngine()

    # Pre-populate preferences as RequestHandler would do
    engine.preferences["tool_name"] = "search_web"
    engine.preferences["tool_args"] = {"query": "merlot"}

    state = ExecutingState()
    output = state.respond(engine, "Please run this tool")

    # 1. Model narration must appear
    assert output == "Executing: MODEL_NARRATION"

    # 2. tool_output is stored
    assert engine.preferences["tool_output"] == "RESULT:search_web:{'query': 'merlot'}"

    # 3. Tool was executed exactly once
    assert engine.request_handler.calls == [
        ("search_web", {"query": "merlot"}, "tester")
    ]

    # 4. Transition → SummarizingState occurred
    assert isinstance(engine.state, SummarizingState)


def test_executing_no_tool_selected_gracefully_skips_execution():
    """
    If no tool_name is present, ExecutingState should skip execution,
    still build a prompt, still call the model, still transition to SummarizingState.
    """
    engine = DummyEngine()

    state = ExecutingState()
    out = state.respond(engine, "Nothing to execute")

    # Returned model narration
    assert out == "Executing: MODEL_NARRATION"

    # tool_output should exist but be None (post-refactor behaviour)
    assert engine.preferences.get("tool_output") is None

    # Model still narrates; transition still occurs
    assert isinstance(engine.state, SummarizingState)

    # Tool handler should not be called
    assert engine.request_handler.calls == []