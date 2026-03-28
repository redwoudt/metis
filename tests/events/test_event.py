from datetime import timezone

from metis.events import Event


def test_event_create_populates_required_fields():
    event = Event.create(
        event_type="command.completed",
        source="ExecutingState",
        correlation_id="corr-123",
        payload={"command_name": "search_wine"},
        metadata={"user_id": "user-1"},
    )

    assert event.event_id
    assert event.event_type == "command.completed"
    assert event.source == "ExecutingState"
    assert event.correlation_id == "corr-123"
    assert event.payload == {"command_name": "search_wine"}
    assert event.metadata == {"user_id": "user-1"}
    assert event.severity == "INFO"
    assert event.tags == []
    assert event.parent_event_id is None
    assert event.timestamp.tzinfo == timezone.utc


def test_event_create_uses_defaults_for_optional_fields():
    event = Event.create(
        event_type="prompt.received",
        source="RequestHandler",
        correlation_id="corr-456",
    )

    assert event.payload == {}
    assert event.metadata == {}
    assert event.severity == "INFO"
    assert event.tags == []
    assert event.parent_event_id is None


def test_event_create_accepts_optional_extensions():
    event = Event.create(
        event_type="task.failed",
        source="Worker",
        correlation_id="corr-789",
        payload={"task_id": "task-1"},
        metadata={"created_by": "user-2"},
        severity="ERROR",
        tags=["scheduler", "background"],
        parent_event_id="parent-123",
    )

    assert event.event_type == "task.failed"
    assert event.source == "Worker"
    assert event.correlation_id == "corr-789"
    assert event.payload["task_id"] == "task-1"
    assert event.metadata["created_by"] == "user-2"
    assert event.severity == "ERROR"
    assert event.tags == ["scheduler", "background"]
    assert event.parent_event_id == "parent-123"