from __future__ import annotations

from typing import Any, Callable


class TaskExecutorRegistry:
    """
    Registry of task executors keyed by task type.

    Scheduled tasks are stored as durable task records that describe what
    should happen later. The registry resolves each task record into the
    concrete execution logic needed to perform that work.

    This keeps task storage separate from task execution and allows the
    scheduling subsystem to support multiple task types over time.
    """

    def __init__(self):
        # Mapping of task_type -> callable responsible for executing it.
        self._executors: dict[str, Callable[..., Any]] = {}

    def register(self, task_type: str, executor: Callable[..., Any]) -> None:
        """
        Register an executor callable for a task type.

        The executor will be called later by the worker when a scheduled task
        of the given type becomes due.
        """
        self._executors[task_type] = executor

    def execute(self, task, context: Any = None) -> Any:
        """
        Execute a scheduled task using its registered executor.

        Raises:
            ValueError: if no executor has been registered for task.task_type.
        """
        executor = self._executors.get(task.task_type)
        if executor is None:
            raise ValueError(f"No executor registered for task type '{task.task_type}'.")

        return executor(task, context=context)