from metis.events import Event, EventBus


class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


def test_subscribe_notifies_matching_observer():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe("command.completed", observer)

    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-1",
    )
    bus.publish(event)

    assert observer.events == [event]


def test_subscribe_does_not_notify_for_non_matching_event_type():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe("command.completed", observer)

    event = Event.create(
        event_type="command.failed",
        source="ExecutingState",
        correlation_id="corr-2",
    )
    bus.publish(event)

    assert observer.events == []


def test_subscribe_all_notifies_for_any_event():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe_all(observer)

    event_1 = Event.create(
        event_type="prompt.received",
        source="RequestHandler",
        correlation_id="corr-3",
    )
    event_2 = Event.create(
        event_type="model.responded",
        source="ModelManager",
        correlation_id="corr-3",
    )

    bus.publish(event_1)
    bus.publish(event_2)

    assert observer.events == [event_1, event_2]


def test_publish_notifies_global_and_typed_observers():
    bus = EventBus()
    global_observer = SpyObserver()
    typed_observer = SpyObserver()

    bus.subscribe_all(global_observer)
    bus.subscribe("command.completed", typed_observer)

    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-4",
    )
    bus.publish(event)

    assert global_observer.events == [event]
    assert typed_observer.events == [event]


def test_unsubscribe_removes_typed_subscription():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe("command.completed", observer)
    bus.unsubscribe("command.completed", observer)

    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-5",
    )
    bus.publish(event)

    assert observer.events == []


def test_unsubscribe_all_removes_global_subscription():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe_all(observer)
    bus.unsubscribe_all(observer)

    event = Event.create(
        event_type="prompt.received",
        source="RequestHandler",
        correlation_id="corr-6",
    )
    bus.publish(event)

    assert observer.events == []


def test_duplicate_typed_subscription_is_ignored():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe("command.completed", observer)
    bus.subscribe("command.completed", observer)

    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-7",
    )
    bus.publish(event)

    assert observer.events == [event]


def test_duplicate_global_subscription_is_ignored():
    bus = EventBus()
    observer = SpyObserver()

    bus.subscribe_all(observer)
    bus.subscribe_all(observer)

    event = Event.create(
        event_type="response.generated",
        source="RequestHandler",
        correlation_id="corr-8",
    )
    bus.publish(event)

    assert observer.events == [event]


def test_has_subscribers_reports_typed_subscriptions_only():
    bus = EventBus()
    observer = SpyObserver()

    assert bus.has_subscribers("command.completed") is False

    bus.subscribe("command.completed", observer)

    assert bus.has_subscribers("command.completed") is True
    assert bus.has_subscribers("command.failed") is False


def test_clear_removes_all_subscriptions():
    bus = EventBus()
    typed_observer = SpyObserver()
    global_observer = SpyObserver()

    bus.subscribe("command.completed", typed_observer)
    bus.subscribe_all(global_observer)
    bus.clear()

    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-9",
    )
    bus.publish(event)

    assert typed_observer.events == []
    assert global_observer.events == []