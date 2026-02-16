"""
Tests for tool selection + preference propagation.

This file was failing after the refactor because it:
1) Loaded the wrong session id ("u1" instead of the user_id used in handle_prompt)
2) (In other tests) referenced the old internal API (engine.request_handler). We avoid that here by
   asserting against the engine's public state (`engine.preferences`).
"""

from metis.handler.request_handler import RequestHandler
from tests.test_utils import setup_test_registry


def test_request_handler_populates_tool_preferences(monkeypatch):
    setup_test_registry(monkeypatch)
    handler = RequestHandler()

    user_id = "user_1"

    # This DSL input should be parsed by the tool-selection layer and stored in engine.preferences.
    handler.handle_prompt(
        user_id=user_id,
        user_input='[tool: search_web][args:{"query":"pinot"}] run search',
    )

    # IMPORTANT: load the same session we just wrote to (must match user_id).
    session = handler.session_manager.load_or_create(user_id)
    engine = session.engine
    assert engine is not None

    # The engine owns preferences; do not reach into old internals like engine.request_handler.
    assert engine.preferences["tool_name"] == "search_web"
    assert engine.preferences["tool_args"]["query"] == "pinot"