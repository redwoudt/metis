# tests/pipeline/test_full_conversation_pipeline.py
"""
Full integration test of the entire conversation pipeline:
Greeting → Clarifying → Executing → Summarizing → Greeting

This test verifies:
- DSL-based tool selection
- state transitions
- command execution
- model narration
- final loop returning to GreetingState
"""

from metis.handler.request_handler import RequestHandler
from metis.states.greeting import GreetingState
from metis.states.clarifying import ClarifyingState
from metis.states.executing import ExecutingState
from metis.states.summarizing import SummarizingState
from metis.conversation_engine import ConversationEngine


# -------------------------------------------------------------------
# Dummy model + services patch for predictable behavior
# -------------------------------------------------------------------

class DummyModelManager:
    """
    Fake model manager providing deterministic responses for every state.
    """
    def __init__(self, response="MODEL"):
        self.response = response

    def generate(self, prompt, **kwargs):
        return self.response


class DummyServiceContainer:
    """Services stub for CoR pipeline."""
    def __init__(self):
        self.quota = None
        self.audit_logger = None


class DummyToolHandler:
    """
    Fake tool executor:

    ExecutingState.execute_tool() will call:
    handler.execute_tool(tool_name, args, user, services)
    """
    def __init__(self):
        self.calls = []

    def execute_tool(self, tool_name, args, user, services):
        self.calls.append((tool_name, args, user))
        return f"TOOL_OUTPUT:{tool_name}:{args}"


# -------------------------------------------------------------------
# Monkeypatched conversation engine for deterministic behavior
# -------------------------------------------------------------------

class DummyEngine(ConversationEngine):
    def __init__(self):
        # engine.model_manager overridden per-test below
        self.preferences = {}
        self.user_id = "tester"
        self.request_handler = DummyToolHandler()
        self.state = GreetingState()

    def set_state(self, new_state):
        self.state = new_state

    def generate_with_model(self, prompt_text):
        return self.model_manager.generate(prompt_text)


# -------------------------------------------------------------------
# THE TEST
# -------------------------------------------------------------------

def test_full_pipeline_end_to_end(monkeypatch):
    """
    Complete flow simulation:

    1. GreetingState responds
    2. ClarifyingState selects tool from DSL
    3. ExecutingState runs tool + generates model narration
    4. SummarizingState narrates and returns us to GreetingState
    """

    # Ensure Config.services() returns our dummy service container
    from metis import config as metis_config
    monkeypatch.setattr(metis_config.Config, "services", lambda: DummyServiceContainer())

    # Monkeypatch ConversationEngine to make everything deterministic
    monkeypatch.setattr(
        "metis.handler.request_handler.ConversationEngine",
        lambda model_manager: DummyEngine()
    )

    # Monkeypatch ModelFactory to always return our dummy model manager
    from metis.models import model_factory
    monkeypatch.setattr(model_factory, "ModelFactory", MagicMockForModelFactory := type(
        "MockFactory",
        (),
        {"for_role": staticmethod(lambda role, cfg: DummyModelManager("MODEL_" + role))}
    ))

    handler = RequestHandler()

    # ------------------------------------------------------------------
    # TURN 1: GREETING
    # ------------------------------------------------------------------
    out1 = handler.handle_prompt("u1", "Hello")
    assert "model_greeting" in out1.lower()  # MODEL_greeting mapped via for_role

    session = handler.session_manager.load_or_create("u1")
    engine = session.engine
    assert isinstance(engine.state, ClarifyingState)

    # ------------------------------------------------------------------
    # TURN 2: CLARIFYING — choose tool via DSL
    # ------------------------------------------------------------------
    out2 = handler.handle_prompt(
        "u1",
        "[tool: search_web][args:{\"query\":\"riesling\"}] please run this"
    )

    # ClarifyingState returns MODEL_clarifying
    assert "model_clarifying" in out2.lower()

    # Tool selected in preferences (will be executed next turn)
    assert engine.preferences["tool_name"] == "search_web"
    assert engine.preferences["tool_args"]["query"] == "riesling"

    # State should now be ExecutingState
    assert isinstance(engine.state, ExecutingState)

    # ------------------------------------------------------------------
    # TURN 3: EXECUTING — run tool + model narration
    # ------------------------------------------------------------------
    out3 = handler.handle_prompt("u1", "Ok go ahead")

    # Should be model narration for executing
    assert "model_executing" in out3.lower()

    # Tool executed
    assert engine.preferences["tool_output"] == "TOOL_OUTPUT:search_web:{'query': 'riesling'}"
    assert engine.request_handler.calls == [
        ("search_web", {"query": "riesling"}, "tester")
    ]

    # State should now be SummarizingState
    assert isinstance(engine.state, SummarizingState)

    # ------------------------------------------------------------------
    # TURN 4: SUMMARIZING — final transition back to GreetingState
    # ------------------------------------------------------------------
    out4 = handler.handle_prompt("u1", "wrap it up")

    assert "model_summarizing" in out4.lower()
    assert isinstance(engine.state, GreetingState)

    # ------------------------------------------------------------------
    # Pipeline complete!
    # ------------------------------------------------------------------
    assert True  # If we've reached here without errors, the flow is correct.