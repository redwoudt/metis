"""Trace one correlated event sequence through the Mêtis EventBus."""

from __future__ import annotations

import logging

from metis.events import AnalyticsObserver, Event, EventBus, MetricsObserver


class FailingObserver:
    """Observer used to demonstrate isolated delivery failures."""

    def notify(self, event: Event) -> None:
        raise RuntimeError(f"demonstration failure for {event.event_type}")


def run_demo() -> dict[str, int | bool]:
    """Publish one request lifecycle and summarize the observed results."""
    bus = EventBus()
    analytics = AnalyticsObserver()
    prompt_metrics = MetricsObserver()
    delivered_after_failure = AnalyticsObserver()

    # Observe the full lifecycle and one selected event type.
    bus.subscribe_all(analytics)
    bus.subscribe("prompt.received", prompt_metrics)

    # A later observer should still receive this event.
    bus.subscribe("model.responded", FailingObserver())
    bus.subscribe("model.responded", delivered_after_failure)

    correlation_id = "chapter11-demo"
    events = (
        Event.create(
            event_type="prompt.received",
            source="ConversationMediator",
            correlation_id=correlation_id,
            payload={"content_length": 24},
        ),
        Event.create(
            event_type="model.responded",
            source="ModelManager",
            correlation_id=correlation_id,
            payload={"duration_ms": 18, "response_length": 42},
        ),
        Event.create(
            event_type="response.generated",
            source="ConversationMediator",
            correlation_id=correlation_id,
            payload={"response_length": 42},
        ),
    )

    # Keep the intentional failure outside the example's stable output.
    bus_logger = logging.getLogger("metis.events.bus")
    previous_level = bus_logger.level
    bus_logger.setLevel(logging.CRITICAL + 1)
    try:
        for event in events:
            bus.publish(event)
    finally:
        bus_logger.setLevel(previous_level)

    correlation_ids = {event.correlation_id for event in analytics.events}
    return {
        "events_published": len(analytics.events),
        "prompt.received_count": prompt_metrics.get_count("prompt.received"),
        "shared_correlation": correlation_ids == {correlation_id},
        "dispatch_continued": (
            delivered_after_failure.get_event_count("model.responded") == 1
        ),
    }


def main() -> int:
    result = run_demo()
    for key, value in result.items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
