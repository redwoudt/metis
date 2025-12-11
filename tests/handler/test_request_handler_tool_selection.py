from metis.handler.request_handler import RequestHandler
from tests.test_utils import setup_test_registry


def test_request_handler_populates_tool_preferences(monkeypatch):
    setup_test_registry(monkeypatch)
    handler = RequestHandler()

    handler.handle_prompt(
        user_id="u1",
        user_input="[tool: search_web][args:{\"query\":\"pinot\"}] run search"
    )

    session = handler.session_manager.load_or_create("u1")
    engine = session.engine

    assert engine.preferences["tool_name"] == "search_web"
    assert engine.preferences["tool_args"]["query"] == "pinot"