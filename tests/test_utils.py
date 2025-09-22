import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("metis.strategy.mock_strategy")

from metis.strategy.base import PromptStrategy
from metis.policy.base import Policy


class MockPromptStrategy(PromptStrategy):
    def __init__(self):
        super().__init__()
        logger.info("[MockPromptStrategy] Initialized")
    def determine_state_name(self, input_text: str, context: dict) -> str:
        logger.info("[MockPromptStrategy] determine_state_name called with input: %s", input_text)
        return "greeting"  # or "summarizing", etc. depending on what state you want to test
    def build_prompt(self, session, user_input):
        if user_input.startswith("[task:"):
            logger.info("[MockPromptStrategy] build_prompt called with user_input: %s", user_input)
            return f"[MockPrompt] {user_input}"
        logger.info("[MockPromptStrategy] build_prompt called with user_input: %s", user_input)
        return f"[MockPrompt] {user_input}"


class AllowAllPolicy(Policy):
    def enforce(self, user_id, request):
        pass


class DenyAllPolicy(Policy):
    def enforce(self, user_id, request):
        raise PermissionError("Access Denied by Policy")


class MockModel:
    """
    A simple mock model to simulate `generate()` calls for testing purposes.
    Records all inputs and returns a predictable string output.
    """
    instantiation_count = 0

    def __init__(self, model_id="mock", log=False, **kwargs):
        self.__class__.instantiation_count += 1
        self.model_id = model_id
        self.kwargs = kwargs
        self.call_log = []
        self.logger = logging.getLogger("metis.models.logging_mock") if log else None

    def generate(self, prompt, **kwargs):
        if self.logger:
            self.logger.info("[proxy] LoggingMockModel generate called with prompt: %s", prompt)
        self.call_log.append(prompt)
        return f"Mocked: {prompt}"

    def __call__(self, prompt, **kwargs):
        return self.generate(prompt, **kwargs)

    def respond(self, prompt):
        self.call_log.append(prompt)
        return f"Response to: {prompt}"

    @classmethod
    def reset(cls):
        cls.instantiation_count = 0

    def __str__(self):
        return f"MockModel(id={self.model_id})"

    def __eq__(self, other):
        return isinstance(other, MockModel) and self.model_id == other.model_id


class LoggingMockModel(MockModel):
    logger = logging.getLogger("metis.models.logging_mock")

    def generate(self, prompt, **kwargs):
        if self.logger:
            self.logger.info("[proxy] LoggingMockModel generate called with prompt: %s", prompt)
        self.call_log.append(prompt)
        return f"Mocked: {prompt}"

    def __call__(self, prompt, **kwargs):
        if self.logger:
            self.logger.info("LoggingMockModel called with prompt: %s", prompt)
        return self.generate(prompt, **kwargs)


def mock_model_factory(**kwargs):
    return MockModel(**kwargs)

def logging_model_factory(**kwargs):
    return MockModel(log=True, **kwargs)


factory_counter = {"count": 0}
def mock_singleton_factory(**kwargs):
    factory_counter["count"] += 1
    return MockModel()


_shared_instance = MockModel()

def cached_model_factory():
    if not hasattr(cached_model_factory, "_shared_instance"):
        cached_model_factory._shared_instance = MockModel(log=True)
    return cached_model_factory._shared_instance

def reset_cached_model_factory():
    cached_model_factory._shared_instance = MockModel()


def rate_limited_model_factory(**kwargs):
    import time
    if not hasattr(rate_limited_model_factory, "_last_call_time"):
        rate_limited_model_factory._last_call_time = 0
    current = time.time()
    if current - rate_limited_model_factory._last_call_time < 1:
        raise Exception("Rate limit exceeded")
    rate_limited_model_factory._last_call_time = current
    return MockModel(log=True)
rate_limited_model_factory._last_call_time = 0

def reset_rate_limited_model_factory():
    rate_limited_model_factory._last_call_time = 0


def create_mock_model(**kwargs):
    return MockModel()

def create_summarize_model(**kwargs):
    class SummarizeModel(MockModel):
        def generate(self, prompt, **kwargs):
            return f"Summary: {prompt[:40]}..."
    return SummarizeModel()

def factory_greeting(**kwargs):
    return MockModel(response="Mocked: Hello from GreetingState!", **kwargs)


class MockSession:
    """
    A lightweight mock of a session object for conversation testing.
    """
    def __init__(self):
        self.persona = ""
        self.tone = ""
        self.context = ""
        self.tool_output = ""
        self.state = ""
        self.engine = MockConversationEngine()


class MockConversationEngine:
    """
    A mock conversation engine for simulating responses and snapshots.
    """
    def __init__(self):
        self.prompts = []
        self.model = MockModel()

    def respond(self, prompt):
        self.prompts.append(prompt)
        return f"Response to: {prompt}"

    def create_snapshot(self):
        return {"mock_snapshot": True}

    def restore_snapshot(self, snapshot):
        self.prompts.append(f"[Restored] {snapshot}")

    def set_model(self, model):
        self.model = model

    def get_model(self):
        return self.model


# --- Test Registry Setup ---
from metis.config import Config

def setup_test_registry(monkeypatch):
    monkeypatch.setenv("METIS_VENDOR", "mock")
    """
    Injects common mock models into the global MODEL_REGISTRY for test usage.
    """
    monkeypatch.setitem(Config.MODEL_REGISTRY, "mock", {
        "vendor": "mock",
        "model": "mock-model",
        "defaults": {},
        "policies": {},
        "factory": create_mock_model
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "summarize", {
        "vendor": "mock",
        "model": "summarizer-v1",
        "defaults": {},
        "policies": {},
        "factory": create_summarize_model
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "log-test", {
        "vendor": "mock",
        "model": "loggable",
        "defaults": {},
        "policies": {"log": True},
        "factory": logging_model_factory
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "cache-test", {
        "vendor": "mock",
        "model": "cachable",
        "defaults": {},
        "policies": {"cache": True},
        "factory": cached_model_factory
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "rate-limit-test", {
        "vendor": "mock",
        "model": "ratelimited",
        "defaults": {},
        "policies": {"max_rps": 1},
        "factory": rate_limited_model_factory
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "singleton-test", {
        "vendor": "mock",
        "model": "singleton-v1",
        "defaults": {},
        "policies": {},
        "factory": mock_singleton_factory
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "analysis", {
        "vendor": "mock",
        "model": "analysis-mock",
        "defaults": {},
        "policies": {},
        "factory": create_mock_model
    })

    monkeypatch.setitem(Config.MODEL_REGISTRY, "greeting", {
        "vendor": "mock",
        "model": "mock-greeting",
        "defaults": {},
        "policies": {},
        "factory": factory_greeting
    })

def factory_loggable(**kwargs):
    return LoggingMockModel(log=True, **kwargs)

# Returns the cached_model_factory() instance for test use
def factory_cache(**kwargs):
    return cached_model_factory()

def factory_ratelimit(**kwargs):
    return rate_limited_model_factory(**kwargs)

__all__ = [
    "MockPromptStrategy", "AllowAllPolicy", "DenyAllPolicy",
    "MockModel", "LoggingMockModel", "mock_model_factory", "logging_model_factory",
    "mock_singleton_factory", "cached_model_factory", "rate_limited_model_factory",
    "create_mock_model", "create_summarize_model", "MockSession", "MockConversationEngine",
    "setup_test_registry", "reset_cached_model_factory", "reset_rate_limited_model_factory",
    "factory_loggable", "factory_cache", "factory_ratelimit", "factory_greeting"
]
