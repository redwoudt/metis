from types import SimpleNamespace

from metis.events import EventBus
from metis.states.executing import ExecutingState


class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


class DummyModelManager:
    def generate(self, prompt_text, **kwargs):
        return "MODEL_NARRATION"


class DummyHandler:
    def __init__(self):
        self.calls = []
        self.config = {"tools": []}

    def execute_tool(self, tool_name, args, user, services):
        self.calls.append((tool_name, args, user))
        return f"RESULT:{tool_name}:{args}"


class DummyEngine:
    def __init__(self):
        self.preferences = {
            "tool_name": "search_web",
            "tool_args": {"query": "merlot"},
            "correlation_id": "corr-exec-1",
        }
        self.user_id = "tester"
        self.request_handler = DummyHandler()
        self.model_manager = DummyModelManager()
        self.state = None

    def generate_with_model(self, prompt_text: str, **kwargs) -> str:
        return self.model_manager.generate(prompt_text, **kwargs)

    def set_state(self, new_state):
        self.state = new_state


def test_executing_state_emits_command_started_and_completed(monkeypatch):
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe_all(spy)

    services = SimpleNamespace(event_bus=bus)

    monkeypatch.setattr(
        "metis.states.executing.metis_config.Config.services",
        staticmethod(lambda: services),
    )

    engine = DummyEngine()
    state = ExecutingState()

    out = state.respond(engine, "please run this tool")

    assert out == "Executing: MODEL_NARRATION"

    event_types = [event.event_type for event in spy.events]
    assert "command.started" in event_types
    assert "command.completed" in event_types

    started = next(event for event in spy.events if event.event_type == "command.started")
    completed = next(event for event in spy.events if event.event_type == "command.completed")

    assert started.payload["command_name"] == "search_web"
    assert completed.payload["command_name"] == "search_web"
    assert started.correlation_id == "corr-exec-1"
    assert completed.correlation_id == "corr-exec-1"