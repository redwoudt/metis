from __future__ import annotations

from typing import Any
from uuid import uuid4

from metis.events import Event

from .clock import Clock
from .retry import RetryPolicy, FixedDelayRetryPolicy
from .scheduler import BackgroundCommand, TaskScheduler, TaskStatus


class Worker:
    """
    Background worker responsible for executing due tasks.

    The scheduler decides when tasks are eligible to run. The worker is
    responsible for retrieving due tasks, executing them, and updating their
    lifecycle state.

    Task execution can happen in two ways:
    - through a task executor registry, which dispatches by task type
    - through the task's fallback `execute()` method when no registry is set
    """

    def __init__(
        self,
        scheduler: TaskScheduler,
        clock: Clock | None = None,
        retry_policy: RetryPolicy | None = None,
        executor_registry: Any = None,
        event_bus: Any = None,
    ):
        self.scheduler = scheduler
        self.clock = clock or Clock()
        self.retry_policy = retry_policy or FixedDelayRetryPolicy()
        self.executor_registry = executor_registry
        self.event_bus = event_bus

    def _publish_task_event(
        self,
        task: BackgroundCommand,
        event_type: str,
        *,
        severity: str = "INFO",
        extra_payload: dict | None = None,
    ) -> None:
        """
        Publish a task lifecycle event when an EventBus is configured.

        Worker owns task execution state transitions, so it is the correct
        publisher for task.started / task.completed / task.failed / task.retried
        / task.abandoned events.
        """
        if self.event_bus is None:
            return

        correlation_id = None
        if isinstance(task.payload, dict):
            correlation_id = task.payload.get("correlation_id")
        if not correlation_id:
            correlation_id = str(uuid4())

        payload = {
            "task_id": task.id,
            "task_type": task.task_type,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
            "retries": task.retries,
            "max_retries": task.max_retries,
        }
        if extra_payload:
            payload.update(extra_payload)

        self.event_bus.publish(
            Event.create(
                event_type=event_type,
                source="Worker",
                correlation_id=correlation_id,
                payload=payload,
                metadata={
                    "created_by": task.created_by,
                },
                severity=severity,
            )
        )

    def run_once(self, context: Any = None) -> list[BackgroundCommand]:
        """
        Execute all tasks that are due right now.

        Why run_once instead of an infinite loop?
        - easier to test
        - easier to embed in chapter examples
        - can later be wrapped by a real daemon/process supervisor loop
        """
        processed: list[BackgroundCommand] = []

        for task in self.scheduler.next_due_tasks(self.clock.now()):
            processed.append(self._execute_task(task, context=context))

        return processed

    def _execute_task(self, task: BackgroundCommand, context: Any = None) -> BackgroundCommand:
        """
        Execute one task and update its lifecycle state.

        If an executor registry is configured, the worker delegates execution
        to the registered executor for the task's type. Otherwise it falls
        back to the task's own `execute()` implementation.

        State transitions handled here:
        - SCHEDULED -> RUNNING
        - RUNNING -> COMPLETED on success
        - RUNNING -> SCHEDULED on retryable failure
        - RUNNING -> ABANDONED after max retries
        """
        task.status = TaskStatus.RUNNING
        self.scheduler.save(task)
        self._publish_task_event(task, "task.started")

        try:
            if self.executor_registry is not None:
                task.result = self.executor_registry.execute(task, context=context)
            else:
                task.result = task.execute(context)
            task.status = TaskStatus.COMPLETED
            task.last_error = None
            self._publish_task_event(
                task,
                "task.completed",
                extra_payload={
                    "result_present": task.result is not None,
                },
            )
        except Exception as exc:
            task.last_error = str(exc)
            task.retries += 1
            self._publish_task_event(
                task,
                "task.failed",
                severity="ERROR",
                extra_payload={
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                },
            )

            # Retry if still within the allowed attempt budget.
            if task.retries <= task.max_retries:
                task.status = TaskStatus.SCHEDULED
                task.scheduled_for = self.clock.now() + self.retry_policy.next_delay(task.retries)
                self._publish_task_event(
                    task,
                    "task.retried",
                    severity="WARNING",
                    extra_payload={
                        "next_scheduled_for": task.scheduled_for.isoformat()
                        if hasattr(task.scheduled_for, "isoformat")
                        else str(task.scheduled_for),
                    },
                )
            else:
                # Give up permanently after max retries.
                task.status = TaskStatus.ABANDONED
                self._publish_task_event(
                    task,
                    "task.abandoned",
                    severity="ERROR",
                )

        self.scheduler.save(task)
        return task