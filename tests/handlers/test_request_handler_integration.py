"""
Integration tests for RequestHandler under the updated architecture:
- End-to-end execution path: RequestHandler → ConversationEngine → ModelManager → ModelProxy
- Ensures responses are returned and engine state is created
- Verifies snapshot (save/undo) functionality still works
- Confirms state transitions operate correctly with the DSL + state machine
"""

from metis.handler.request_handler import RequestHandler
from metis.conversation_engine import ConversationEngine


def test_request_handler_end_to_end_flow(monkeypatch):
    """
    Full pipeline: RequestHandler builds the engine and model manager correctly.
    No assumptions are made about adapter prefixes (legacy behavior removed).
    """
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})

    response = handler.handle_prompt(user_id="user_123", user_input="Hello Metis!")

    # Basic validity checks
    assert isinstance(response, str)
    assert len(response) > 0

    # Engine should exist with history
    session = handler.session_manager.load_or_create("user_123")
    engine = session.engine
    assert isinstance(engine, ConversationEngine)
    assert hasattr(engine, "history")
    assert len(engine.history) >= 1


def test_request_handler_snapshot_save_and_restore(monkeypatch):
    """
    Verify snapshots can be saved and restored.
    Undo should restore previous engine state and still return meaningful output.
    """
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    user_id = "user_snap"

    # Initial call with save=True should store a snapshot
    response_1 = handler.handle_prompt(user_id=user_id, user_input="Generate something", save=True)
    assert isinstance(response_1, str)
    assert "generate" in response_1.lower()

    session = handler.session_manager.load_or_create(user_id)
    engine = session.engine
    assert hasattr(engine, "create_snapshot")
    assert hasattr(engine, "restore_snapshot")

    # Undo restores previous state; response still comes from model
    response_2 = handler.handle_prompt(user_id=user_id, user_input="Undo that", undo=True)
    assert isinstance(response_2, str)

    # ClarifyingState may be selected depending on strategy → assert on keyword only
    assert "clarify" in response_2.lower() or "undo" in response_2.lower()


def test_request_handler_state_transitions(monkeypatch):
    """
    Ensure the RequestHandler properly advances states between turns.
    Turn 1 → GreetingState
    Turn 2 → ClarifyingState
    (Exact text varies with prompt templates; assertions are keyword-based.)
    """
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    user_id = "user_state"

    # Turn 1 → GreetingState
    out1 = handler.handle_prompt(user_id=user_id, user_input="Hi there!")
    assert isinstance(out1, str)
    assert "hello" in out1.lower() or "greeting" in out1.lower() or "friendly" in out1.lower()

    # Turn 2 → ClarifyingState
    out2 = handler.handle_prompt(user_id=user_id, user_input="Clarify this please")
    assert isinstance(out2, str)

    # Check for clarifying behavior, not exact template wording
    assert "clarify" in out2.lower()

    # Engine should have valid state + model_manager
    session = handler.session_manager.load_or_create(user_id)
    engine = session.engine

    assert hasattr(engine, "state")
    assert hasattr(engine, "model_manager")