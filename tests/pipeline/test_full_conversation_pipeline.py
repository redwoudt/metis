# tests/pipeline/test_full_conversation_pipeline.py
"""
Full integration test of the entire conversation pipeline with permissions enabled:
Greeting → Clarifying → Executing → Summarizing → Greeting

This test verifies:
- DSL-based tool selection
- permission gating via PermissionHandler
- command execution (via the engine's tool executor surface)
- audit + quota wiring
- state transitions
"""

from metis.handler.request_handler import RequestHandler
from metis.states.greeting import GreetingState
from metis.states.clarifying import ClarifyingState
from metis.states.executing import ExecutingState
from metis.states.summarizing import SummarizingState
from metis.conversation_engine import ConversationEngine


# -------------------------------------------------------------------
# Dummy model + services
# -------------------------------------------------------------------

class DummyModelManager:
    """Deterministic model responses per role."""
    def __init__(self, response):
        self.response = response

    def generate(self, prompt, **kwargs):
        return self.response


class DummyQuota:
    """Quota that always allows execution."""
    def allow(self, user_id, tool_name):
        return True


class DummyAuditLogger:
    """Audit logger that records events."""
    def __init__(self):
        self.events = []

    def info(self, msg):
        self.events.append(msg)


class DummyServiceContainer:
    """Services used by the strict pipeline."""
    def __init__(self):
        self.quota = DummyQuota()
        self.audit_logger = DummyAuditLogger()


class DummyToolExecutor:
    """
    Fake tool executor.

    ClarifyingState inspects:
        engine.tool_executor.config["tools"]
    ExecutingState calls:
        engine.tool_executor.execute_tool(...)
    """
    def __init__(self):
        self.calls = []
        self.config = {
            "tools": ["search_web"]
        }

    def execute_tool(self, tool_name, args, user, services):
        self.calls.append((tool_name, args, user))
        return f"TOOL_OUTPUT:{tool_name}:{args}"


# -------------------------------------------------------------------
# Dummy engine
# -------------------------------------------------------------------

class DummyEngine(ConversationEngine):
    """
    Lightweight ConversationEngine stub that matches the post-refactor
    engine surface used by states:
      - engine.preferences
      - engine.tool_executor
      - engine.generate_with_model(...)
      - engine.set_state(...)
    """
    def __init__(self):
        self.preferences = {}
        self.user_id = "tester"
        self.tool_executor = DummyToolExecutor()
        self.state = GreetingState()
        self.model_manager = None

    def set_state(self, new_state):
        self.state = new_state

    def generate_with_model(self, prompt_text):
        return self.model_manager.generate(prompt_text)


# -------------------------------------------------------------------
# THE TEST
# -------------------------------------------------------------------

def test_full_pipeline_with_permissions(monkeypatch):
    """
    End-to-end pipeline test with PermissionHandler enabled.
    """

    # ------------------------------------------------------------------
    # Patch services container (quota + audit)
    # ------------------------------------------------------------------
    from metis import config as metis_config
    monkeypatch.setattr(
        metis_config.Config,
        "services",
        lambda: DummyServiceContainer()
    )

    # ------------------------------------------------------------------
    # Patch engine creation (RequestHandler → Session → Engine)
    # ------------------------------------------------------------------
    monkeypatch.setattr(
        "metis.handler.request_handler.ConversationEngine",
        lambda model_manager: DummyEngine()
    )

    # ------------------------------------------------------------------
    # Patch model factory (deterministic per-role output)
    # ------------------------------------------------------------------
    from metis.models import model_factory
    monkeypatch.setattr(
        model_factory,
        "ModelFactory",
        type(
            "MockFactory",
            (),
            {
                "for_role": staticmethod(
                    lambda role, cfg: DummyModelManager(f"MODEL_{role}")
                )
            },
        ),
    )

    handler = RequestHandler()
    user_id = "user_1"

    # ------------------------------------------------------------------
    # TURN 1: GREETING
    # ------------------------------------------------------------------
    out1 = handler.handle_prompt(user_id, "Hello")

    # Do NOT assert exact strings — assert semantic intent
    assert "greeting" in out1.lower()

    session = handler.session_manager.load_or_create(user_id)
    engine = session.engine
    assert isinstance(engine.state, ClarifyingState)

    # ------------------------------------------------------------------
    # TURN 2: CLARIFYING (select tool)
    # ------------------------------------------------------------------
    out2 = handler.handle_prompt(
        user_id,
        '[tool: search_web][args:{"query":"riesling"}]'
    )

    assert "clarifying" in out2.lower()
    assert engine.preferences["tool_name"] == "search_web"
    assert isinstance(engine.state, ExecutingState)

    # Inject permission metadata as policy layer would
    engine.preferences["metadata"] = {
        "allow_user_tools": True
    }

    # ------------------------------------------------------------------
    # TURN 3: EXECUTING (permission + quota enforced)
    # ------------------------------------------------------------------
    out3 = handler.handle_prompt(user_id, "Go ahead")

    assert "executing" in out3.lower()
    assert engine.preferences["tool_output"] == (
        "TOOL_OUTPUT:search_web:{'query': 'riesling'}"
    )

    # Tool was executed
    assert engine.tool_executor.calls == [
        ("search_web", {"query": "riesling"}, "tester")
    ]

    assert isinstance(engine.state, SummarizingState)

    # ------------------------------------------------------------------
    # TURN 4: SUMMARIZING
    # ------------------------------------------------------------------
    out4 = handler.handle_prompt(user_id, "wrap it up")

    assert out4.startswith("Summary:")
    assert isinstance(engine.state, GreetingState)