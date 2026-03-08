from __future__ import annotations

from typing import Any

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
    ):
        self.scheduler = scheduler
        self.clock = clock or Clock()
        self.retry_policy = retry_policy or FixedDelayRetryPolicy()
        self.executor_registry = executor_registry

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

        try:
            if self.executor_registry is not None:
                task.result = self.executor_registry.execute(task, context=context)
            else:
                task.result = task.execute(context)
            task.status = TaskStatus.COMPLETED
            task.last_error = None
        except Exception as exc:
            task.last_error = str(exc)
            task.retries += 1

            # Retry if still within the allowed attempt budget.
            if task.retries <= task.max_retries:
                task.status = TaskStatus.SCHEDULED
                task.scheduled_for = self.clock.now() + self.retry_policy.next_delay(task.retries)
            else:
                # Give up permanently after max retries.
                task.status = TaskStatus.ABANDONED

        self.scheduler.save(task)
        return task