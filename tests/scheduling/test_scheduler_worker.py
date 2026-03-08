from datetime import datetime, timezone, timedelta

from metis.scheduling.clock import TestClock
from metis.scheduling.retry import FixedDelayRetryPolicy
from metis.scheduling.scheduler import BackgroundCommand, InMemoryTaskScheduler, TaskStatus
from metis.scheduling.worker import Worker


def test_worker_executes_due_task():
    """
    A task scheduled for 'now' should be picked up and completed by the worker.
    """
    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    worker = Worker(scheduler=scheduler, clock=clock)

    task = BackgroundCommand(
        description="Summarize inbox",
        scheduled_for=clock.now(),
    )
    scheduler.schedule(task)

    processed = worker.run_once()

    assert len(processed) == 1
    saved = scheduler.get(task.id)
    assert saved is not None
    assert saved.status == TaskStatus.COMPLETED
    assert saved.result["delivered"] is True


def test_worker_retries_failed_task():
    """
    A failing task should be rescheduled when retry budget remains.
    """
    class FailingTask(BackgroundCommand):
        def execute(self, context=None):
            raise RuntimeError("temporary failure")

    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    retry_policy = FixedDelayRetryPolicy(delay=timedelta(minutes=5))
    worker = Worker(scheduler=scheduler, clock=clock, retry_policy=retry_policy)

    task = FailingTask(
        description="Retry me",
        scheduled_for=clock.now(),
        max_retries=2,
    )
    scheduler.schedule(task)

    worker.run_once()

    saved = scheduler.get(task.id)
    assert saved is not None
    assert saved.status == TaskStatus.SCHEDULED
    assert saved.retries == 1
    assert saved.last_error == "temporary failure"
    assert saved.scheduled_for == clock.now() + timedelta(minutes=5)