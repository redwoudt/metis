"""
Unit and integration tests for the RequestHandler orchestration flow.
Includes success paths, policy rejection, tool execution, session lifecycle,
mock tracing, exception handling, and snapshot-style output checks.
"""

import pytest
from unittest.mock import MagicMock
from metis.handler import RequestHandler
from metis.exceptions import ToolExecutionError
from tests.test_utils import (
    MockPromptStrategy,
    AllowAllPolicy,
    DenyAllPolicy,
    factory_greeting,
    factory_loggable,
    factory_logging,
    setup_test_registry,
    cached_model_factory,
    rate_limited_model_factory,
    mock_singleton_factory,
    logging_model_factory,
    mock_model_factory,
    MockModel,
    reset_cached_model_factory,
    factory_cache,
    factory_ratelimit,
    reset_rate_limited_model_factory,
)

from metis.config import Config
from metis.states.greeting import GreetingState
from tests.test_utils import LoggingMockModel

@pytest.fixture(autouse=True)
def clear_session_manager_state():
    """
    Safely clear session state for all active users if SessionManager supports it.
    """
    from metis.components.session_manager import SessionManager

    manager = SessionManager()
    # Attempt to clear known sessions from the current manager instance
    try:
        sessions = getattr(manager, "_sessions", None)
        if isinstance(sessions, dict):
            for s in sessions.values():
                s.state = None
                if hasattr(s, "engine"):
                    s.engine.state = None
                    s.engine = None
            sessions.clear()
    except Exception:
        pass
    yield

def test_handle_prompt_success(monkeypatch):
    setup_test_registry(monkeypatch)

    # Patch strategy to return 'greeting'
    def mock_determine_state_name(self, input_text, context):
        return "greeting"

    monkeypatch.setattr(MockPromptStrategy, "determine_state_name", mock_determine_state_name)

    strategy = MockPromptStrategy()
    handler = RequestHandler(strategy=strategy, policy=AllowAllPolicy())

    session = handler.session_manager.load_or_create("user_123")
    session.state = None
    session.engine = None

    # Patch session manager to:
    # - force determine_state_name to be used
    # - inject correct model role (to trigger mock model)
    original_load = handler.session_manager.load_or_create

    def load_and_set_state(user_id):
        session = original_load(user_id)
        from metis.states.greeting import GreetingState
        session.state = GreetingState()
        session.engine = None
        setattr(session, "context", "")  # optional
        setattr(session, "tone", "friendly")  # optional
        setattr(session, "persona", "Helpful Assistant")  # optional
        return session

    handler.session_manager.load_or_create = load_and_set_state

    # Patch model factory to force role mapping to 'greeting'
    monkeypatch.setitem(Config.MODEL_REGISTRY, "greeting", {
        "vendor": "mock",
        "model": "mock-greeting",
        "defaults": {},
        "policies": {},
        "factory": factory_greeting,
    })

    # Call handler
    response = handler.handle_prompt("user_123", "Tell me something nice")

    # Validate response
    assert "friendly" in response

def test_policy_enforcement_denied():
    handler = RequestHandler(policy=DenyAllPolicy())
    with pytest.raises(PermissionError):
        handler.handle_prompt("user_123", "Forbidden access")


def test_weather_tool_execution(monkeypatch):
    setup_test_registry(monkeypatch)
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    response = handler.handle_prompt("user_456", "What’s the weather like today?")
    assert "weather" in response.lower() or "Weather Info" in response


def test_session_lifecycle_and_prompt_building(monkeypatch):
    setup_test_registry(monkeypatch)
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    user_id = "user_test"
    prompt = "Summarize yesterday's session"
    first_response = handler.handle_prompt(user_id, prompt)
    assert "Summarize the following input" in first_response
    assert "Summarize yesterday" in first_response  # or use escaped string


def test_tool_execution_exception_handling():
    mock_executor = MagicMock()
    mock_executor.execute.side_effect = Exception("Simulated tool failure")

    handler = RequestHandler(
        strategy=MockPromptStrategy(),
        policy=AllowAllPolicy(),
        tool_executor=mock_executor,
    )

    with pytest.raises(ToolExecutionError) as exc:
        handler.handle_prompt("user_789", "Check the weather")
    assert "Simulated tool failure" in str(exc.value)


def test_tracing_output_snapshot(monkeypatch):
    setup_test_registry(monkeypatch)
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    user_id = "user_snap"
    session = handler.session_manager.load_or_create(user_id)
    session.state = None
    session.engine = None
    prompt = "Explain quantum mechanics"
    response = handler.handle_prompt(user_id, prompt)
    # Debug assertion: ConversationEngine should have 'model' after handle_prompt
    session = handler.session_manager.load_or_create(user_id)
    assert hasattr(session.engine, "model"), "ConversationEngine is missing 'model' attribute"
    assert "Explain quantum mechanics" in response
    assert "friendly" in response


def test_model_factory_is_used(monkeypatch):
    setup_test_registry(monkeypatch)
    from metis.models.model_proxy import ModelProxy

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    handler.handle_prompt("user_proxy", "[task:mock] Summarize this for me")
    result = handler.handle_prompt("user_proxy", "[task:mock] Summarize this for me")
    session = handler.session_manager.load_or_create("user_proxy")
    model_used = session.engine.get_model()
    assert isinstance(model_used, ModelProxy)


def test_singleton_model_is_reused(monkeypatch):
    from metis.config import Config
    from metis.models import singleton_cache
    from metis.states.greeting import GreetingState

    singleton_cache._instance_cache.clear()
    monkeypatch.setenv("METIS_VENDOR", "mock")
    monkeypatch.setitem(__import__("metis.config").config.Config.MODEL_REGISTRY, "greeting", {
        "vendor": "mock",
        "model": "test-greeting",
        "defaults": {},
        "policies": {},
        "factory": mock_model_factory
    })

    # Reset MockModel instantiation counter before test
    MockModel.instantiation_count = 0

    monkeypatch.setitem(Config.MODEL_REGISTRY, "singleton-test", {
        "vendor": "mock",
        "model": "singleton-v1",
        "defaults": {},
        "policies": {},
        "factory": mock_singleton_factory
    })

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    handler.handle_prompt("user_singleton", "[task:singleton-test] First call")
    session = handler.session_manager.load_or_create("user_singleton")
    handler.handle_prompt("user_singleton", "[task:singleton-test] Second call")

    assert MockModel.instantiation_count == 1

def test_proxy_logs_prompt(monkeypatch, caplog):
    setup_test_registry(monkeypatch)

    # Register logging mock model config
    monkeypatch.setitem(Config.MODEL_REGISTRY, "log-test", {
        "vendor": "mock",
        "model": "loggable",
        "defaults": {},
        "policies": {"log": True},
        "factory": factory_logging,
    })

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    session = handler.session_manager.load_or_create("user_log")
    session.state = GreetingState()
    session.engine = None

    caplog.set_level("DEBUG", logger="metis.models.logging_mock")

    handler.handle_prompt("user_log", "[task:log-test] Hello there")

    assert any("Prompt constructed:" in r.message for r in caplog.records)

@pytest.mark.usefixtures("clear_session_manager_state")
def test_proxy_caches_responses(monkeypatch):
    reset_cached_model_factory()
    setup_test_registry(monkeypatch)

    monkeypatch.setitem(Config.MODEL_REGISTRY, "cache-test", {
        "vendor": "mock",
        "model": "cachable",
        "defaults": {},
        "policies": {"cache": True},
        "factory": factory_cache
    })

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    session = handler.session_manager.load_or_create("user_cache")
    session.state = GreetingState()
    session.engine = None

    handler.handle_prompt("user_cache", "[task:cache-test] Say hi")
    handler.handle_prompt("user_cache", "[task:cache-test] Say hi")

    model = handler.session_manager.load_or_create("user_cache").engine.get_model()
    assert hasattr(model.backend, "call_log")
    assert len(model.backend.call_log) == 1


@pytest.mark.usefixtures("clear_session_manager_state")
def test_proxy_rate_limit(monkeypatch):
    reset_rate_limited_model_factory()
    setup_test_registry(monkeypatch)

    monkeypatch.setitem(Config.MODEL_REGISTRY, "rate-limit-test", {
        "vendor": "mock",
        "model": "ratelimited",
        "defaults": {},
        "policies": {"max_rps": 1},
        "factory": factory_ratelimit
    })

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    session = handler.session_manager.load_or_create("user_rate")
    session.state = GreetingState()
    session.engine = None

    handler.handle_prompt("user_rate", "[task:rate-limit-test] call 1")

    with pytest.raises(Exception, match="Rate limit exceeded"):
        handler.handle_prompt("user_rate", "[task:rate-limit-test] call 2")
