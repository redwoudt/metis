from datetime import datetime, timedelta, timezone

import pytest

from metis.commands.schedule import ScheduleTaskCommand
from metis.commands.base import ToolContext
from metis.scheduling.clock import TestClock
from metis.scheduling.scheduler import (
    BackgroundCommand,
    InMemoryTaskScheduler,
    TaskStatus,
    parse_schedule_time,
)


class Services:
    """
    Small test-only services object that provides exactly what the command needs.

    This keeps the unit test focused and avoids depending on the full application
    services container.
    """

    def __init__(self, clock, scheduler):
        self.clock = clock
        self.scheduler = scheduler


def test_schedule_task_creates_background_task():
    """
    schedule_task should now create a real BackgroundCommand and persist it in
    the scheduler, rather than returning a placeholder success response.
    """
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    services = Services(clock=clock, scheduler=scheduler)

    command = ScheduleTaskCommand()
    context = ToolContext(
        command=command,
        args={
            "time": "in 10 minutes",
            "description": "Generate summary",
        },
        user="user_123",
        services=services,
    )

    result = command.execute(context)

    assert result["scheduled"] is True
    assert result["status"] == TaskStatus.SCHEDULED

    task = scheduler.get(result["task_id"])
    assert task is not None
    assert task.description == "Generate summary"
    assert task.created_by == "user_123"


def test_parse_schedule_time_normalizes_iso_timestamp_to_utc():
    now = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    parsed = parse_schedule_time("2026-01-01T12:00:00+02:00", now)

    assert parsed == datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    assert parsed.utcoffset() == timedelta(0)


def test_background_command_rejects_naive_scheduled_time():
    with pytest.raises(ValueError, match="scheduled_for must be timezone-aware"):
        BackgroundCommand(
            description="Ambiguous local time",
            scheduled_for=datetime(2026, 1, 1, 9, 0),
        )
