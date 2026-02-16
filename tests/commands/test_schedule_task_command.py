import pytest
from metis.commands.schedule import ScheduleTaskCommand
from metis.commands.base import ToolContext


def test_schedule_task_ok():
    """
    Happy-path test for ScheduleTaskCommand.

    Post-refactor, ScheduleTaskCommand:
    - does NOT execute scheduling side effects itself
    - validates intent
    - returns a normalized scheduling payload
    """

    cmd = ScheduleTaskCommand()

    ctx = ToolContext(
        command=cmd,
        user="user_1",
        args={
            # Refactored argument names
            "description": "send_reminder",
            "time": "tomorrow",
        },
    )

    out = cmd.execute(ctx)

    assert out["scheduled"] is True
    assert out["description"] == "send_reminder"
    assert out["time"] == "tomorrow"


def test_schedule_task_requires_time():
    """
    Guard-rail test:
    The command must fail fast if required scheduling
    information is missing.
    """

    cmd = ScheduleTaskCommand()

    ctx = ToolContext(
        command=cmd,
        user="user_1",
        args={},  # missing required fields
    )

    with pytest.raises(ValueError):
        cmd.execute(ctx)