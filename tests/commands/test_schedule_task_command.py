import pytest
from metis.commands.tasks import ScheduleTaskCommand
from metis.commands.base import ToolContext


def test_schedule_task_ok(monkeypatch):
    cmd = ScheduleTaskCommand()

    # Mock scheduler
    scheduled = {}
    def fake_schedule(t, a):
        scheduled["tool"] = t
        scheduled["args"] = a

    monkeypatch.setattr(cmd, "_schedule", fake_schedule)

    ctx = ToolContext(
        command=cmd,
        args={"task": "send_reminder", "when": "tomorrow"},
        user="u1"
    )

    out = cmd.execute(ctx)

    assert out["status"] == "scheduled"
    assert scheduled["tool"] == "send_reminder"
    assert scheduled["args"]["when"] == "tomorrow"


def test_schedule_task_requires_task_name():
    cmd = ScheduleTaskCommand()
    ctx = ToolContext(command=cmd, args={}, user="u1")
    with pytest.raises(ValueError):
        cmd.execute(ctx)