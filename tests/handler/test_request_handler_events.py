from types import SimpleNamespace

from metis.events import EventBus
from metis.handler.request_handler import RequestHandler


class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


class DummySession:
    def __init__(self):
        self.tool_preferences = {}
        self.persona = ""
        self.tone = ""
        self.context = ""
        self.state = None
        self.engine = None


def test_request_handler_emits_request_lifecycle_events(monkeypatch):
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe_all(spy)

    services = SimpleNamespace(event_bus=bus)

    monkeypatch.setattr(
        "metis.handler.request_handler.Config.services",
        staticmethod(lambda: services),
    )

    captured = {}

    def fake_respond(self, user_input: str):
        captured["correlation_id"] = self.preferences.get("correlation_id")
        return "ok"

    monkeypatch.setattr(
        "metis.conversation_engine.ConversationEngine.respond",
        fake_respond,
        raising=True,
    )

    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    handler.session_manager.load_or_create = lambda user_id: DummySession()
    handler.session_manager.save = lambda user_id, session: None

    out = handler.handle_prompt(user_id="u1", user_input="hello")

    assert out == "ok"

    event_types = [event.event_type for event in spy.events]
    assert "prompt.received" in event_types
    assert "response.generated" in event_types

    prompt_event = next(event for event in spy.events if event.event_type == "prompt.received")
    response_event = next(event for event in spy.events if event.event_type == "response.generated")

    assert prompt_event.metadata["user_id"] == "u1"
    assert response_event.metadata["user_id"] == "u1"
    assert prompt_event.correlation_id == response_event.correlation_id
    assert captured["correlation_id"] == prompt_event.correlation_id