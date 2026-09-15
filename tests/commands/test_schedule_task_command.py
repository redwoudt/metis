from datetime import datetime, timezone

import pytest

from metis.commands.base import ToolContext
from metis.commands.schedule import ScheduleTaskCommand
from metis.scheduling.clock import TestClock
from metis.scheduling.scheduler import InMemoryTaskScheduler, TaskStatus


class Services:
    """
    Minimal test services container for schedule command tests.
    """

    def __init__(self, clock, scheduler):
        self.clock = clock
        self.scheduler = scheduler


def test_schedule_task_ok():
    """
    ScheduleTaskCommand should create and persist a real background task.
    """
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    services = Services(clock=clock, scheduler=scheduler)

    cmd = ScheduleTaskCommand()

    ctx = ToolContext(
        command=cmd,
        user="user_1",
        args={
            "description": "send_reminder",
            "time": "tomorrow",
        },
        services=services,
    )

    out = cmd.execute(ctx)

    assert out["scheduled"] is True
    assert out["description"] == "send_reminder"
    assert out["time"] == "tomorrow"
    assert out["status"] == TaskStatus.SCHEDULED

    task = scheduler.get(out["task_id"])
    assert task is not None
    assert task.description == "send_reminder"
    assert task.created_by == "user_1"


def test_schedule_task_requires_time():
    """
    The command should fail fast when required scheduling information is missing.
    """
    cmd = ScheduleTaskCommand()

    ctx = ToolContext(
        command=cmd,
        user="user_1",
        args={},
    )

    with pytest.raises(ValueError):
        cmd.execute(ctx)


def test_scheduled_tool_preserves_request_and_effect_identities():
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    services = Services(clock=clock, scheduler=scheduler)
    command = ScheduleTaskCommand()

    result = command.execute(
        ToolContext(
            command=command,
            user="user_1",
            args={
                "description": "Search later",
                "time": "in 10 minutes",
                "tool_name": "search_web",
                "task_args": {"query": "Penelope"},
            },
            metadata={
                "correlation_id": "request-10",
                "idempotency_key": "effect-10",
            },
            services=services,
        )
    )

    task = scheduler.get(result["task_id"])
    assert task is not None
    assert task.payload["correlation_id"] == "request-10"
    assert task.payload["idempotency_key"] == "effect-10"


def test_scheduled_tool_uses_task_id_when_no_identity_is_supplied():
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    services = Services(clock=clock, scheduler=scheduler)
    command = ScheduleTaskCommand()

    result = command.execute(
        ToolContext(
            command=command,
            user="user_1",
            args={
                "description": "Search later",
                "time": "in 10 minutes",
                "tool_name": "search_web",
                "task_args": {"query": "Odysseus"},
            },
            services=services,
        )
    )

    task = scheduler.get(result["task_id"])
    assert task is not None
    assert task.payload["correlation_id"] == task.id
    assert task.payload["idempotency_key"] == task.id
