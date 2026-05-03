from types import SimpleNamespace

from metis.events import EventBus
from metis.mediator import ConversationMediator


class DummySession:
    def __init__(self):
        self.tool_preferences = {}
        self.persona = ""
        self.tone = ""
        self.context = ""
        self.state = None
        self.engine = None


class DummySessionManager:
    def __init__(self):
        self.session = DummySession()
        self.saved = []

    def load_or_create(self, user_id):
        return self.session

    def save(self, user_id, session):
        self.saved.append((user_id, session))


class AllowPolicy:
    def enforce(self, user_id, user_input):
        return None



class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


# DummyToolExecutor for tool_executor injection tests
class DummyToolExecutor:
    def execute_tool(self, tool_name, args=None, user=None, services=None):
        return {"result": "ok"}


def test_mediator_runs_request_lifecycle(monkeypatch):
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe_all(spy)

    services = SimpleNamespace(event_bus=bus)

    monkeypatch.setattr(
        "metis.mediator.conversation_mediator.Config.services",
        staticmethod(lambda: services),
    )

    monkeypatch.setattr(
        "metis.conversation_engine.ConversationEngine.respond",
        lambda self, user_input: f"ok:{user_input}",
        raising=True,
    )

    session_manager = DummySessionManager()
    mediator = ConversationMediator(
        session_manager=session_manager,
        policy=AllowPolicy(),
        config={"vendor": "mock", "model": "stub", "policies": {}},
    )

    response = mediator.handle_request("u1", "[tone: warm] hello")

    assert response == "ok:hello"
    assert session_manager.saved == [("u1", session_manager.session)]
    assert session_manager.session.tone == "warm"

    event_types = [event.event_type for event in spy.events]
    assert "prompt.received" in event_types
    assert "response.generated" in event_types

    prompt_event = next(event for event in spy.events if event.event_type == "prompt.received")
    response_event = next(event for event in spy.events if event.event_type == "response.generated")

    assert prompt_event.correlation_id == response_event.correlation_id
    assert prompt_event.metadata["user_id"] == "u1"


def test_mediator_populates_tool_preferences(monkeypatch):
    monkeypatch.setattr(
        "metis.conversation_engine.ConversationEngine.respond",
        lambda self, user_input: "ok",
        raising=True,
    )

    session_manager = DummySessionManager()
    mediator = ConversationMediator(
        session_manager=session_manager,
        policy=AllowPolicy(),
        config={"vendor": "mock", "model": "stub", "policies": {}},
    )

    mediator.handle_request(
        "u1",
        '[tool: search_web][args:{"query":"pinot"}] run search',
    )

    session = session_manager.session

    assert session.tool_preferences["tool_name"] == "search_web"
    assert session.tool_preferences["tool_args"]["query"] == "pinot"
    assert session.engine.preferences["tool_name"] == "search_web"
    assert session.engine.preferences["tool_args"]["query"] == "pinot"


def test_mediator_publishes_failure_event(monkeypatch):
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe_all(spy)

    services = SimpleNamespace(event_bus=bus)

    monkeypatch.setattr(
        "metis.mediator.conversation_mediator.Config.services",
        staticmethod(lambda: services),
    )

    class DenyPolicy:
        def enforce(self, user_id, user_input):
            raise PermissionError("blocked")

    mediator = ConversationMediator(
        session_manager=DummySessionManager(),
        policy=DenyPolicy(),
        config={"vendor": "mock", "model": "stub", "policies": {}},
    )

    try:
        mediator.handle_request("u1", "hello")
    except PermissionError:
        pass

    event_types = [event.event_type for event in spy.events]

    assert "prompt.received" in event_types
    assert "response.failed" in event_types

    failed_event = next(event for event in spy.events if event.event_type == "response.failed")
    assert failed_event.payload["error_type"] == "PermissionError"


# Test: ConversationMediator injects tool_executor without execute_tool compatibility method
def test_mediator_injects_tool_executor_without_execute_tool_compatibility(monkeypatch):
    """
    ConversationMediator should inject ToolExecutor into the engine without
    adding the old engine.execute_tool compatibility method.
    """
    tool_executor = DummyToolExecutor()
    services = SimpleNamespace(event_bus=None, tool_executor=tool_executor)

    monkeypatch.setattr(
        "metis.mediator.conversation_mediator.Config.services",
        staticmethod(lambda: services),
    )

    captured = {}

    def fake_respond(self, user_input):
        captured["engine"] = self
        return "ok"

    monkeypatch.setattr(
        "metis.conversation_engine.ConversationEngine.respond",
        fake_respond,
        raising=True,
    )

    session_manager = DummySessionManager()
    mediator = ConversationMediator(
        session_manager=session_manager,
        policy=AllowPolicy(),
        config={"vendor": "mock", "model": "stub", "policies": {}},
    )

    response = mediator.handle_request("u1", "hello")

    assert response == "ok"
    engine = captured["engine"]
    assert engine.tool_executor is tool_executor
    assert engine.services is services
    assert engine.user_id == "u1"
    assert not hasattr(engine, "execute_tool")