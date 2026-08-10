import pytest

from metis.events import Event, EventBus, EventPublisher, NullEventPublisher


def make_event() -> Event:
    return Event.create(
        event_type="model.requested",
        source="ModelManager",
        correlation_id="corr-chapter-15",
    )


@pytest.mark.parametrize("publisher_type", [EventBus, NullEventPublisher])
def test_publishers_share_the_publishing_contract(publisher_type):
    publisher = publisher_type()

    assert isinstance(publisher, EventPublisher)
    assert publisher.publish(make_event()) is None


def test_null_publisher_retains_no_instance_state():
    publisher = NullEventPublisher()

    publisher.publish(make_event())

    assert not hasattr(publisher, "__dict__")
