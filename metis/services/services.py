import logging
import os
from pathlib import Path

from metis.scheduling.clock import Clock
from metis.scheduling.executors import TaskExecutorRegistry
from metis.scheduling.retry import FixedDelayRetryPolicy
from metis.scheduling.scheduler import InMemoryTaskScheduler, SQLiteTaskScheduler
from metis.scheduling.worker import Worker


class QuotaService:
    """
    Extremely simple quota and usage tracker for tool execution.
    """

    def __init__(self, limit_per_user: int = 100):
        self.limit_per_user = limit_per_user
        self.usage = {}

    def allow(self, user_id: str, tool_name: str) -> bool:
        """
        Return True when the given user is still allowed to execute tools.
        """
        count = self.usage.get(user_id, 0)
        if count >= self.limit_per_user:
            return False
        self.usage[user_id] = count + 1
        return True


def execute_tool_task(task, context=None):
    """
    Execute a scheduled tool task using the standard RequestHandler tool path.

    The task payload is expected to contain:
    - tool_name: name of the registered tool command to execute
    - args: arguments for the tool command
    - user: optional user identifier; falls back to task.created_by
    """
    payload = task.payload or {}
    tool_name = payload.get("tool_name")
    args = payload.get("args", {})
    user = payload.get("user", task.created_by)

    if not tool_name:
        raise ValueError("tool_command task requires 'tool_name' in payload.")

    # Lazy import to avoid circular import during application startup.
    from metis.handler.request_handler import RequestHandler

    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    return handler.execute_tool(tool_name, args=args, user=user, services=get_services())


def execute_generic_task(task, context=None):
    """
    Execute a generic scheduled task.

    This provides a simple default executor for scheduled tasks that do not
    need to call back into the tool pipeline. It is useful for demonstrations,
    smoke tests, and generic background work that only needs to record that it
    was processed successfully.
    """
    return {
        "delivered": True,
        "description": task.description,
        "task_type": task.task_type,
        "payload": dict(task.payload or {}),
    }


class Services:
    """
    Shared services container used by command execution and scheduling.
    """

    def __init__(self):
        self.quota = QuotaService()
        self.audit_logger = logging.getLogger("metis.audit")

        self.clock = Clock()
        self.retry_policy = FixedDelayRetryPolicy()

        scheduler_backend = os.getenv("METIS_TASK_SCHEDULER", "sqlite").lower()
        sqlite_path = Path(os.getenv("METIS_TASK_DB", ".metis/tasks.db"))

        if scheduler_backend == "inmemory":
            self.scheduler = InMemoryTaskScheduler(clock=self.clock)
        else:
            self.scheduler = SQLiteTaskScheduler(db_path=sqlite_path, clock=self.clock)

        self.executor_registry = TaskExecutorRegistry()
        self.executor_registry.register("generic", execute_generic_task)
        self.executor_registry.register("tool_command", execute_tool_task)

        self.worker = Worker(
            scheduler=self.scheduler,
            clock=self.clock,
            retry_policy=self.retry_policy,
            executor_registry=self.executor_registry,
        )


_services_singleton = Services()


def get_services() -> Services:
    """
    Return the shared service container.
    """
    return _services_singleton