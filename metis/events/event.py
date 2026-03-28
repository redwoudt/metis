from __future__ import annotations

"""
Structured event model for Mêtis.

The Event class provides a stable schema for all system events emitted by
publishers such as RequestHandler, ExecutingState, ModelManager, and Worker.

Why this exists:
- Plain dictionaries drift over time and become inconsistent
- Observers should rely on a predictable event envelope
- Correlation IDs let us trace a single request across multiple components
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Event:
    """
    A structured event emitted by a publisher in the system.

    Fields:
        event_id:
            Unique identifier for this event instance.

        event_type:
            Stable event name, e.g. "command.completed" or "model.failed".

        timestamp:
            UTC timestamp indicating when the event was created.

        source:
            Name of the emitting component, e.g. "RequestHandler".

        correlation_id:
            Shared identifier used to link related events across a single
            request or workflow.

        payload:
            Event-specific data describing what happened.

        metadata:
            Shared contextual information, such as user_id, session_id,
            environment, model name, feature flags, etc.

        severity:
            Optional signal describing event importance. Examples:
            "INFO", "WARNING", "ERROR".

        tags:
            Optional labels for filtering and grouping.

        parent_event_id:
            Optional reference to an earlier event in the same causal chain.
    """

    event_id: str
    event_type: str
    timestamp: datetime
    source: str
    correlation_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    severity: str = "INFO"
    tags: list[str] = field(default_factory=list)
    parent_event_id: str | None = None

    @classmethod
    def create(
        cls,
        event_type: str,
        source: str,
        correlation_id: str,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        severity: str = "INFO",
        tags: list[str] | None = None,
        parent_event_id: str | None = None,
    ) -> "Event":
        """
        Convenience factory for creating a new Event.

        This method standardizes:
        - event ID generation
        - UTC timestamp creation
        - default payload / metadata / tags handling

        Args:
            event_type:
                Stable event name such as "prompt.received".

            source:
                Component emitting the event, such as "ExecutingState".

            correlation_id:
                Identifier used to tie related events together.

            payload:
                Event-specific details. Defaults to an empty dict.

            metadata:
                Shared contextual data. Defaults to an empty dict.

            severity:
                Importance level for the event. Defaults to "INFO".

            tags:
                Optional labels for filtering/grouping.

            parent_event_id:
                Optional reference to a preceding event.

        Returns:
            A fully populated Event instance.
        """
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            source=source,
            correlation_id=correlation_id,
            payload=payload or {},
            metadata=metadata or {},
            severity=severity,
            tags=tags or [],
            parent_event_id=parent_event_id,
        )