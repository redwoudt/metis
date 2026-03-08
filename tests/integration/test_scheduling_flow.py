from datetime import datetime, timezone

from metis.commands.base import ToolContext
from metis.commands.schedule import ScheduleTaskCommand
from metis.scheduling.clock import TestClock
from metis.scheduling.scheduler import SQLiteTaskScheduler, TaskStatus
from metis.scheduling.worker import Worker


class Services:
    """
    Minimal services container for scheduling integration tests.
    """

    def __init__(self, clock, scheduler):
        self.clock = clock
        self.scheduler = scheduler


def test_schedule_list_and_run_generic_task(tmp_path):
    """
    End-to-end flow:
    - schedule a task through ScheduleTaskCommand
    - list it through the scheduler
    - execute it through the worker
    - verify persisted completed state
    """
    db_path = tmp_path / "tasks.db"
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = SQLiteTaskScheduler(db_path=db_path, clock=clock)
    services = Services(clock=clock, scheduler=scheduler)

    command = ScheduleTaskCommand()
    context = ToolContext(
        command=command,
        user="user_123",
        args={
            "description": "Generate summary",
            "time": "now",
        },
        services=services,
    )

    result = command.execute(context)
    task_id = result["task_id"]

    scheduled_tasks = scheduler.all_tasks()
    assert len(scheduled_tasks) == 1
    assert scheduled_tasks[0].id == task_id
    assert scheduled_tasks[0].status == TaskStatus.SCHEDULED

    worker = Worker(scheduler=scheduler, clock=clock)
    processed = worker.run_once()

    assert len(processed) == 1

    saved = scheduler.get(task_id)
    assert saved is not None
    assert saved.status == TaskStatus.COMPLETED
    assert saved.result["delivered"] is True
    assert saved.result["description"] == "Generate summary"