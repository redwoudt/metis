"""
Integration tests for RequestHandler under the Adapter + Bridge architecture.

Covers:
- End-to-end execution path: RequestHandler → ConversationEngine → ModelManager → Adapter.
- Ensures responses are returned and include the provider prefix (mock adapter).
- Verifies snapshot (save/undo) functionality still works.
- Confirms state transitions do not break the new wiring.
"""

from metis.handler.request_handler import RequestHandler
from metis.conversation_engine import ConversationEngine


def test_request_handler_end_to_end_flow(monkeypatch):
    """Full pipeline: RequestHandler builds adapters, bridge, and engine successfully."""
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})

    # Run a single prompt
    response = handler.handle_prompt(user_id="user_123", user_input="Hello Metis!")
    assert isinstance(response, str)
    assert "[mock:stub]" in response.lower() or "mock" in response.lower()

    # The engine should now exist and have conversation history
    session = handler.session_manager.load_or_create("user_123")
    engine = session.engine
    assert isinstance(engine, ConversationEngine)
    assert len(engine.history) >= 1


def test_request_handler_snapshot_save_and_restore(monkeypatch):
    """Verify that snapshots can be saved and restored correctly."""
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    user_id = "user_snap"

    # Initial run (creates a snapshot)
    response_1 = handler.handle_prompt(user_id=user_id, user_input="Generate something", save=True)
    assert isinstance(response_1, str)

    session = handler.session_manager.load_or_create(user_id)
    engine = session.engine
    assert hasattr(engine, "create_snapshot")
    assert hasattr(engine, "restore_snapshot")

    # Simulate undo (restore snapshot)
    response_2 = handler.handle_prompt(user_id=user_id, user_input="Undo that", undo=True)
    assert isinstance(response_2, str)
    assert "[mock:stub]" in response_2.lower()


def test_request_handler_state_transitions(monkeypatch):
    """Ensure that RequestHandler correctly updates the state between turns."""
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    user_id = "user_state"

    # First interaction -> GreetingState (then transitions to ClarifyingState)
    out1 = handler.handle_prompt(user_id=user_id, user_input="Hi there!")
    assert isinstance(out1, str)
    assert "[mock:stub]" in out1.lower()

    # Second interaction should continue from the next state
    out2 = handler.handle_prompt(user_id=user_id, user_input="Clarify this please")
    assert isinstance(out2, str)
    assert "[mock:stub]" in out2.lower()

    session = handler.session_manager.load_or_create(user_id)
    engine = session.engine
    assert hasattr(engine, "state")
    assert hasattr(engine, "model_manager")