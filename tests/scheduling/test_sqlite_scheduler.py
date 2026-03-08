from datetime import datetime, timezone

from metis.scheduling.clock import TestClock
from metis.scheduling.scheduler import BackgroundCommand, SQLiteTaskScheduler, TaskStatus


def test_sqlite_scheduler_persists_tasks_across_instances(tmp_path):
    """
    Tasks saved by one scheduler instance should be visible to a later instance
    using the same SQLite database file.
    """
    db_path = tmp_path / "tasks.db"
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))

    scheduler_a = SQLiteTaskScheduler(db_path=db_path, clock=clock)
    task = BackgroundCommand(
        description="Persist me",
        scheduled_for=clock.now(),
        task_type="generic",
    )
    scheduler_a.schedule(task)

    scheduler_b = SQLiteTaskScheduler(db_path=db_path, clock=clock)
    loaded = scheduler_b.get(task.id)

    assert loaded is not None
    assert loaded.id == task.id
    assert loaded.description == "Persist me"
    assert loaded.status == TaskStatus.SCHEDULED