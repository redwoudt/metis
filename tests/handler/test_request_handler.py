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
    factory_loggable,
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


def test_handle_prompt_success(monkeypatch):
    setup_test_registry(monkeypatch)

    # Patch method on class
    def mock_determine_state_name(self, input_text, context):
        context["task"] = "greeting"  # ensure model role aligns
        return "greeting"

    monkeypatch.setattr(MockPromptStrategy, "determine_state_name", mock_determine_state_name)

    strategy = MockPromptStrategy()
    handler = RequestHandler(strategy=strategy, policy=AllowAllPolicy())

    # Force determine_state_name to be called
    session = handler.session_manager.load_or_create("user_123")
    session.state = None

    response = handler.handle_prompt("user_123", "Tell me something nice")

    assert "Mocked:" in response or "Summary:" in response

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
    prompt = "Explain quantum mechanics"
    response = handler.handle_prompt(user_id, prompt)
    # Debug assertion: ConversationEngine should have 'model' after handle_prompt
    session = handler.session_manager.load_or_create(user_id)
    assert hasattr(session.engine, "model"), "ConversationEngine is missing 'model' attribute"
    assert "Explain quantum mechanics" in response
    assert "Provide a clear explanation" in response


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
    monkeypatch.setitem(Config.MODEL_REGISTRY, "log-test", {
        "vendor": "mock",
        "model": "loggable",
        "defaults": {},
        "policies": {"log": True},
        "factory": factory_loggable
    })
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    caplog.set_level("INFO", logger="metis.models.logging_mock")
    handler.handle_prompt("user_log", "[task:log-test] Hello there")

    assert any("LoggingMockModel generate called with prompt" in r.message for r in caplog.records)

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
    response1 = handler.handle_prompt("user_cache", "[task:cache-test] Say hi")
    response2 = handler.handle_prompt("user_cache", "[task:cache-test] Say hi")
    model = handler.session_manager.load_or_create("user_cache").engine.get_model()
    assert hasattr(model, "backend")
    assert len(model.backend.call_log) == 1

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

    # First call should succeed
    handler.handle_prompt("user_rate", "[task:rate-limit-test] call 1")

    # Second call immediately should trigger rate limit
    with pytest.raises(Exception, match="Rate limit exceeded"):
        handler.handle_prompt("user_rate", "[task:rate-limit-test] call 2")