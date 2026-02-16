"""
Updated tests for RequestHandler after migrating to:
- Command Pattern
- Chain of Responsibility tool pipeline
- DSL-based tool/task selection
- New RequestHandler and ConversationEngine behavior

Key change in this file:
- Avoid any references to the *old* engine API (e.g. `engine.request_handler`).
  Tests should interact with RequestHandler directly, or with the engine’s public API
  (e.g. `engine.get_model()`), not internal wiring.
"""

import pytest
from unittest.mock import MagicMock

from metis.handler import RequestHandler
from metis.config import Config
from metis.states.greeting import GreetingState
from metis.models.model_proxy import ModelProxy

from tests.test_utils import (
    MockPromptStrategy,
    AllowAllPolicy,
    DenyAllPolicy,
    setup_test_registry,
    factory_greeting,
    factory_logging,
    factory_cache,
    reset_cached_model_factory,
    reset_rate_limited_model_factory,
    mock_singleton_factory,
)

from tests.test_utils import LoggingMockModel


# -------------------------------------------------------------------------
# FIXTURE — ensure clean session state between tests
# -------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_session_manager_state():
    """
    The SessionManager is implemented as a singleton in Mêtis.
    These tests mutate session state (state/engine), so we must reset between tests
    to avoid order-dependent failures.
    """
    from metis.components.session_manager import SessionManager

    manager = SessionManager()
    sessions = getattr(manager, "_sessions", {})
    for s in sessions.values():
        s.state = None
        if hasattr(s, "engine"):
            s.engine = None
    sessions.clear()
    yield


# -------------------------------------------------------------------------
# BASIC SUCCESS TEST
# -------------------------------------------------------------------------
def test_handle_prompt_success(monkeypatch):
    """
    Sanity test:
    - Given a RequestHandler configured to force GreetingState
    - When we handle a prompt
    - Then we get a friendly response that echoes the user input (per mock model)
    """
    setup_test_registry(monkeypatch)

    # Strategy forces GreetingState
    monkeypatch.setattr(
        MockPromptStrategy,
        "determine_state_name",
        lambda self, text, ctx: "greeting",
    )

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    # Inject greeting model registry entry
    monkeypatch.setitem(
        Config.MODEL_REGISTRY,
        "greeting",
        {
            "vendor": "mock",
            "model": "mock-greeting",
            "defaults": {},
            "policies": {},
            "factory": factory_greeting,
        },
    )

    response = handler.handle_prompt("user_123", "Tell me something nice")

    assert "friendly" in response.lower()
    assert "tell me something nice" in response.lower()


# -------------------------------------------------------------------------
# POLICY ENFORCEMENT
# -------------------------------------------------------------------------
def test_policy_enforcement_denied():
    """
    If the policy denies the request, RequestHandler should raise PermissionError.
    """
    handler = RequestHandler(policy=DenyAllPolicy())
    with pytest.raises(PermissionError):
        handler.handle_prompt("user_123", "Forbidden access")


# -------------------------------------------------------------------------
# SESSION LIFECYCLE + PROMPT BUILDING
# -------------------------------------------------------------------------
def test_session_lifecycle_and_prompt_building(monkeypatch):
    """
    Ensure we can create/load a session and route a prompt through the pipeline.
    This is intentionally high-level (we don’t assert internal engine wiring).
    """
    setup_test_registry(monkeypatch)
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    user_id = "user_test"
    prompt = "[task:summarize] Summarize yesterday’s session"

    r = handler.handle_prompt(user_id, prompt)

    assert isinstance(r, str)
    assert "summarize" in r.lower()
    assert "yesterday" in r.lower()


# -------------------------------------------------------------------------
# MODEL FACTORY IS USED — ModelProxy appears
# -------------------------------------------------------------------------
def test_model_factory_is_used(monkeypatch):
    """
    Regression test for the refactor:
    - We no longer reach into `engine.request_handler` (old API).
    - We validate behavior through the engine public surface (`engine.get_model()`).
    """
    setup_test_registry(monkeypatch)

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    # Use the same user_id consistently (avoid creating a different session by mistake)
    user_id = "user_proxy"

    handler.handle_prompt(user_id, "[task:mock] Summarize something")
    handler.handle_prompt(user_id, "[task:mock] Summarize something")

    session = handler.session_manager.load_or_create(user_id)

    assert session.engine is not None, "Expected ConversationEngine to be created on first handle_prompt()"
    model_used = session.engine.get_model()

    assert isinstance(model_used, ModelProxy)


# -------------------------------------------------------------------------
# SINGLETON MODEL REUSE
# -------------------------------------------------------------------------
def test_singleton_model_is_reused(monkeypatch):
    """
    Ensure a singleton-configured model is instantiated once and reused.
    """
    from metis.models import singleton_cache

    singleton_cache._instance_cache.clear()

    monkeypatch.setitem(
        Config.MODEL_REGISTRY,
        "singleton-test",
        {
            "vendor": "mock",
            "model": "singleton-v1",
            "defaults": {},
            "policies": {},
            "factory": mock_singleton_factory,
        },
    )

    # Reset instantiation count
    from tests.test_utils import MockModel

    MockModel.instantiation_count = 0

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    handler.handle_prompt("user_s", "[task:singleton-test] First call")
    handler.handle_prompt("user_s", "[task:singleton-test] Second call")

    assert MockModel.instantiation_count == 1


# -------------------------------------------------------------------------
# TRACE LOGGING
# -------------------------------------------------------------------------
def test_proxy_logs_prompt(monkeypatch, caplog):
    """
    If the model policies enable logging, the proxy should emit a 'Prompt constructed:' log.
    """
    setup_test_registry(monkeypatch)

    monkeypatch.setitem(
        Config.MODEL_REGISTRY,
        "log-test",
        {
            "vendor": "mock",
            "model": "loggable",
            "defaults": {},
            "policies": {"log": True},
            "factory": factory_logging,
        },
    )

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())

    # Force a known starting state for determinism
    session = handler.session_manager.load_or_create("user_log")
    session.state = GreetingState()
    session.engine = None

    caplog.set_level("DEBUG", logger="metis.models.logging_mock")

    handler.handle_prompt("user_log", "[task:log-test] Hello there")

    assert any("Prompt constructed:" in r.message for r in caplog.records)


# -------------------------------------------------------------------------
# CACHING VIA MODELPROXY
# -------------------------------------------------------------------------
@pytest.mark.usefixtures("clear_session_manager_state")
def test_proxy_caches_responses(monkeypatch):
    """
    If caching is enabled, repeated identical prompts should reuse the same backend
    behind the proxy model.
    """
    reset_cached_model_factory()
    setup_test_registry(monkeypatch)

    monkeypatch.setitem(
        Config.MODEL_REGISTRY,
        "cache-test",
        {
            "vendor": "mock",
            "model": "cachable",
            "defaults": {},
            "policies": {"cache": True},
            "factory": factory_cache,
        },
    )

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    user_id = "user_cache"

    handler.handle_prompt(user_id, "[task:cache-test] Say hi")
    first_engine = handler.session_manager.load_or_create(user_id).engine
    first_model = first_engine.get_model()

    handler.handle_prompt(user_id, "[task:cache-test] Say hi")
    second_engine = handler.session_manager.load_or_create(user_id).engine
    second_model = second_engine.get_model()

    assert first_model.backend is second_model.backend


# -------------------------------------------------------------------------
# RATE LIMITING TEST FOR MODELPROXY
# -------------------------------------------------------------------------
@pytest.mark.usefixtures("clear_session_manager_state")
def test_proxy_rate_limit(monkeypatch, caplog):
    """
    Rate limiting should log a warning when calls happen too quickly.
    This is behavior-level: we do not assert internal engine plumbing.
    """
    # Fake time for deterministic rate limiting
    fake_time = [1000.0]

    def fake_time_fn():
        return fake_time[0]

    monkeypatch.setattr("time.time", fake_time_fn)

    reset_rate_limited_model_factory()
    setup_test_registry(monkeypatch)

    caplog.set_level("WARNING", logger="metis.models.model_proxy")

    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    user_id = "user_rate"

    # First call OK
    handler.handle_prompt(user_id, "[task:rate-limit-test] first call")

    # Same proxy instance reused (engine should stay attached to the session)
    session = handler.session_manager.load_or_create(user_id)
    proxy_model = session.engine.get_model()
    assert proxy_model is session.engine.get_model()

    # Do NOT advance time → immediate second call triggers rate limit
    handler.handle_prompt(user_id, "[task:rate-limit-test] second call")

    assert any("Rate limit exceeded" in r.message for r in caplog.records)