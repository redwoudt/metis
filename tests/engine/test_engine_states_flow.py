# tests/engine/test_engine_states_flow.py

import pytest

from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager


class AskState:
    """First state: asks the model a question, then transitions to AnswerState."""
    def respond(self, engine, user_input: str) -> str:
        out = engine.generate_with_model(f"Q: {user_input}")
        engine.set_state(AnswerState())
        return out


class AnswerState:
    """Second state: answers using the model (stays in this state)."""
    def respond(self, engine, user_input: str) -> str:
        return engine.generate_with_model(f"A: {user_input}")


class NoneState:
    """Returns None to ensure engine coalesces to empty string (defensive behavior)."""
    def respond(self, engine, user_input: str):
        return None


def _engine_with(vendor: str, model: str) -> ConversationEngine:
    client = ModelFactory.for_role("analysis", {"vendor": vendor, "model": model, "policies": {}})
    manager = ModelManager(client)
    return ConversationEngine(model_manager=manager)


def test_state_calls_bridge_and_history_updates():
    engine = _engine_with("mock", "stub")
    engine.set_state(AskState())

    out1 = engine.respond("hello")
    assert isinstance(out1, str)
    assert "[mock:stub]" in out1.lower()
    assert "q: hello" in out1.lower()
    assert len(engine.history) == 1

    out2 = engine.respond("world")  # AnswerState now active
    assert isinstance(out2, str)
    assert "[mock:stub]" in out2.lower()
    assert "a: world" in out2.lower()
    assert len(engine.history) == 2


def test_swapping_model_manager_mid_session_changes_output():
    engine = _engine_with("mock", "A")
    engine.set_state(AnswerState())

    out_a = engine.respond("same input")
    assert "[mock:a]" in out_a.lower()

    # Swap adapter via the Bridge implementor
    client_b = ModelFactory.for_role("analysis", {"vendor": "mock", "model": "B", "policies": {}})
    manager_b = ModelManager(client_b)
    engine.set_model_manager(manager_b)

    out_b = engine.respond("same input")
    assert "[mock:b]" in out_b.lower()
    assert out_a != out_b  # different adapter => different prefix


def test_state_returning_none_is_coalesced_to_empty_string():
    engine = _engine_with("mock", "stub")
    engine.set_state(NoneState())

    out = engine.respond("ignored")
    assert out == ""  # ConversationEngine.respond() coerces None -> ""
    assert len(engine.history) == 1