import pytest

from metis.components.model_manager import ModelManager
from metis.events import EventBus, NullEventPublisher
from metis.models.adapters.mock_adapter import MockAdapter


class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


class FailingModel:
    def respond(self, prompt, **kwargs):
        raise RuntimeError("storm ahead")


class FalseyPublisher:
    def __init__(self):
        self.events = []

    def __bool__(self):
        return False

    def publish(self, event):
        self.events.append(event)


def test_omitted_publisher_selects_null_publisher():
    manager = ModelManager(MockAdapter("chapter-15"))

    assert isinstance(manager.event_bus, NullEventPublisher)


def test_explicit_falsey_publisher_is_not_replaced():
    publisher = FalseyPublisher()
    manager = ModelManager(MockAdapter("chapter-15"), event_bus=publisher)

    manager.generate("Continue")

    assert manager.event_bus is publisher
    assert len(publisher.events) == 2


def test_publisher_choice_does_not_change_model_output():
    client = MockAdapter("chapter-15")

    observed = ModelManager(client, EventBus()).generate("Continue")
    silent = ModelManager(client, NullEventPublisher()).generate("Continue")

    assert observed == silent


def test_real_bus_receives_model_lifecycle_events():
    bus = EventBus()
    observer = SpyObserver()
    bus.subscribe_all(observer)
    manager = ModelManager(MockAdapter("chapter-15"), event_bus=bus)

    manager.generate("Continue", correlation_id="corr-model-15")

    assert [event.event_type for event in observer.events] == [
        "model.requested",
        "model.responded",
    ]
    assert {event.correlation_id for event in observer.events} == {"corr-model-15"}


def test_null_publisher_does_not_suppress_model_failure():
    manager = ModelManager(FailingModel(), event_bus=NullEventPublisher())

    with pytest.raises(RuntimeError, match="storm ahead"):
        manager.generate("Continue")
