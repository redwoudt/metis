import logging

from metis.events import Event
from metis.events import (
    AnalyticsObserver,
    LoggingObserver,
    MetricsObserver,
    SafetyObserver,
)


def test_logging_observer_emits_log_record(caplog):
    observer = LoggingObserver()
    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-1",
        payload={"command_name": "search_wine"},
        metadata={"user_id": "user-1"},
    )

    with caplog.at_level(logging.INFO, logger="metis.events"):
        observer.notify(event)

    assert "command.completed" in caplog.text
    assert "ExecutingState" in caplog.text
    assert "corr-1" in caplog.text


def test_metrics_observer_counts_events():
    observer = MetricsObserver()

    event_1 = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-2",
    )
    event_2 = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-3",
    )

    observer.notify(event_1)
    observer.notify(event_2)

    assert observer.get_count("command.completed") == 2
    assert observer.get_count("command.failed") == 0


def test_metrics_observer_records_average_duration():
    observer = MetricsObserver()

    observer.notify(
        Event.create(
            event_type="model.responded",
            source="ModelManager",
            correlation_id="corr-4",
            payload={"duration_ms": 100},
        )
    )
    observer.notify(
        Event.create(
            event_type="model.responded",
            source="ModelManager",
            correlation_id="corr-5",
            payload={"duration_ms": 300},
        )
    )

    assert observer.get_average_duration("model.responded") == 200
    assert observer.get_average_duration("command.completed") is None


def test_analytics_observer_tracks_events_and_counts():
    observer = AnalyticsObserver()

    event_1 = Event.create(
        event_type="prompt.received",
        source="RequestHandler",
        correlation_id="corr-6",
    )
    event_2 = Event.create(
        event_type="prompt.received",
        source="RequestHandler",
        correlation_id="corr-7",
    )
    event_3 = Event.create(
        event_type="response.generated",
        source="RequestHandler",
        correlation_id="corr-6",
    )

    observer.notify(event_1)
    observer.notify(event_2)
    observer.notify(event_3)

    assert observer.get_event_count("prompt.received") == 2
    assert observer.get_event_count("response.generated") == 1
    assert observer.get_event_count("model.failed") == 0
    assert observer.get_events_by_type("prompt.received") == [event_1, event_2]


def test_safety_observer_tracks_failed_events():
    observer = SafetyObserver()

    failed_event = Event.create(
        event_type="command.failed",
        source="ExecutingState",
        correlation_id="corr-8",
        severity="ERROR",
    )

    observer.notify(failed_event)

    assert observer.get_failures("command.failed") == 1
    assert failed_event in observer.get_flagged_events()


def test_safety_observer_tracks_policy_blocked():
    observer = SafetyObserver()

    blocked_event = Event.create(
        event_type="policy.blocked",
        source="PolicyHandler",
        correlation_id="corr-9",
    )

    observer.notify(blocked_event)

    assert blocked_event in observer.get_flagged_events()


def test_safety_observer_tracks_warning_and_error_events():
    observer = SafetyObserver()

    warning_event = Event.create(
        event_type="task.retried",
        source="Worker",
        correlation_id="corr-10",
        severity="WARNING",
    )
    error_event = Event.create(
        event_type="model.failed",
        source="ModelManager",
        correlation_id="corr-11",
        severity="ERROR",
    )

    observer.notify(warning_event)
    observer.notify(error_event)

    flagged = observer.get_flagged_events()
    assert warning_event in flagged
    assert error_event in flagged