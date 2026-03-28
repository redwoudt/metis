from __future__ import annotations

"""
Concrete observers for Mêtis.

These observers react to events emitted by the system. Each observer
focuses on a single concern:

- LoggingObserver  -> structured logs
- MetricsObserver  -> counters and simple metrics
- AnalyticsObserver -> product / usage insights
- SafetyObserver   -> monitoring for policy or failure signals

Design principles:
- Observers must remain passive (no business logic decisions)
- Observers must not affect core execution flow
- Observers should be simple, composable, and testable
"""

import logging
from collections import defaultdict
from typing import Any

from .event import Event


# -----------------------------------------------------------------------------
# Logging Observer
# -----------------------------------------------------------------------------

logger = logging.getLogger("metis.events")


class LoggingObserver:
    """
    Emits structured logs for every event.

    This observer is typically subscribed globally so that all events are
    recorded consistently.

    In production, this could be extended to:
    - JSON logging
    - external log sinks (ELK, Datadog, etc.)
    """

    def notify(self, event: Event) -> None:
        logger.info(
            "[%s] %s source=%s correlation_id=%s payload=%s metadata=%s severity=%s",
            event.timestamp.isoformat(),
            event.event_type,
            event.source,
            event.correlation_id,
            event.payload,
            event.metadata,
            event.severity,
        )


# -----------------------------------------------------------------------------
# Metrics Observer
# -----------------------------------------------------------------------------

class MetricsObserver:
    """
    Tracks simple in-memory metrics.

    This observer counts how often each event type occurs and can optionally
    track durations if present in payload.

    This is intentionally simple for Mêtis. In production, this would likely
    forward to Prometheus, StatsD, or similar systems.
    """

    def __init__(self) -> None:
        # Count occurrences of each event type
        self.counters: dict[str, int] = defaultdict(int)

        # Track durations (if provided in payload)
        self.durations: dict[str, list[float]] = defaultdict(list)

    def notify(self, event: Event) -> None:
        # Increment counter for this event type
        self.counters[event.event_type] += 1

        # If duration is provided, record it
        duration = event.payload.get("duration_ms")
        if isinstance(duration, (int, float)):
            self.durations[event.event_type].append(duration)

    def get_count(self, event_type: str) -> int:
        """
        Return how many times an event type has occurred.
        """
        return self.counters.get(event_type, 0)

    def get_average_duration(self, event_type: str) -> float | None:
        """
        Return average duration for an event type if available.
        """
        values = self.durations.get(event_type)
        if not values:
            return None
        return sum(values) / len(values)


# -----------------------------------------------------------------------------
# Analytics Observer
# -----------------------------------------------------------------------------

class AnalyticsObserver:
    """
    Captures product and usage-level signals.

    This observer aggregates higher-level insights such as:
    - tool usage frequency
    - model usage
    - command success/failure rates

    In production, this would typically forward events to an external
    analytics pipeline (e.g., Segment, Snowflake, BigQuery).
    """

    def __init__(self) -> None:
        # Simple in-memory aggregation for demonstration
        self.events: list[Event] = []
        self.event_counts: dict[str, int] = defaultdict(int)

    def notify(self, event: Event) -> None:
        self.events.append(event)
        self.event_counts[event.event_type] += 1

    def get_event_count(self, event_type: str) -> int:
        return self.event_counts.get(event_type, 0)

    def get_events_by_type(self, event_type: str) -> list[Event]:
        return [e for e in self.events if e.event_type == event_type]


# -----------------------------------------------------------------------------
# Safety Observer
# -----------------------------------------------------------------------------

class SafetyObserver:
    """
    Monitors high-risk or policy-related events.

    This observer does NOT enforce policy. It observes and records signals
    such as:
    - policy violations
    - repeated failures
    - abnormal system behavior

    It is typically subscribed only to specific high-signal events.
    """

    def __init__(self) -> None:
        # Track flagged or concerning events
        self.flagged_events: list[Event] = []

        # Track counts of critical events
        self.failure_counts: dict[str, int] = defaultdict(int)

    def notify(self, event: Event) -> None:
        # Track explicit failure events
        if event.event_type.endswith(".failed"):
            self.failure_counts[event.event_type] += 1
            self.flagged_events.append(event)

        # Track policy violations
        if event.event_type == "policy.blocked":
            self.flagged_events.append(event)

        # Track high severity events
        if event.severity in ("WARNING", "ERROR"):
            self.flagged_events.append(event)

    def get_failures(self, event_type: str) -> int:
        """
        Return number of failures for a given event type.
        """
        return self.failure_counts.get(event_type, 0)

    def get_flagged_events(self) -> list[Event]:
        """
        Return all flagged events for inspection.
        """
        return list(self.flagged_events)