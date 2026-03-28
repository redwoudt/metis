from datetime import datetime, timedelta, timezone

from metis.events import EventBus
from metis.scheduling.clock import TestClock
from metis.scheduling.retry import FixedDelayRetryPolicy
from metis.scheduling.scheduler import BackgroundCommand, InMemoryTaskScheduler, TaskStatus
from metis.scheduling.worker import Worker


class SpyObserver:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


def test_worker_emits_started_and_completed_events():
    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe_all(spy)

    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    worker = Worker(scheduler=scheduler, clock=clock, event_bus=bus)

    task = BackgroundCommand(
        description="Summarize inbox",
        scheduled_for=clock.now(),
        payload={"correlation_id": "corr-task-1"},
    )
    scheduler.schedule(task)

    processed = worker.run_once()

    assert len(processed) == 1

    event_types = [event.event_type for event in spy.events]
    assert "task.started" in event_types
    assert "task.completed" in event_types

    started = next(event for event in spy.events if event.event_type == "task.started")
    completed = next(event for event in spy.events if event.event_type == "task.completed")

    assert started.correlation_id == "corr-task-1"
    assert completed.correlation_id == "corr-task-1"
    assert completed.payload["task_id"] == task.id


def test_worker_emits_failed_and_retried_events():
    class FailingTask(BackgroundCommand):
        def execute(self, context=None):
            raise RuntimeError("temporary failure")

    bus = EventBus()
    spy = SpyObserver()
    bus.subscribe_all(spy)

    clock = TestClock(datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    scheduler = InMemoryTaskScheduler(clock=clock)
    retry_policy = FixedDelayRetryPolicy(delay=timedelta(minutes=5))
    worker = Worker(
        scheduler=scheduler,
        clock=clock,
        retry_policy=retry_policy,
        event_bus=bus,
    )

    task = FailingTask(
        description="Retry me",
        scheduled_for=clock.now(),
        max_retries=2,
        payload={"correlation_id": "corr-task-2"},
    )
    scheduler.schedule(task)

    worker.run_once()

    event_types = [event.event_type for event in spy.events]
    assert "task.started" in event_types
    assert "task.failed" in event_types
    assert "task.retried" in event_types

    failed = next(event for event in spy.events if event.event_type == "task.failed")
    retried = next(event for event in spy.events if event.event_type == "task.retried")

    assert failed.correlation_id == "corr-task-2"
    assert retried.correlation_id == "corr-task-2"

    saved = scheduler.get(task.id)
    assert saved is not None
    assert saved.status == TaskStatus.SCHEDULED
    assert saved.retries == 1