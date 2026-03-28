import logging
import os
from pathlib import Path

from metis.events import EventBus
from metis.events.observers import (
    AnalyticsObserver,
    LoggingObserver,
    MetricsObserver,
    SafetyObserver,
)

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

    We reuse the shared services container so scheduled tool execution flows
    through the same infrastructure as normal request-driven tool execution.
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

    This is the composition root for cross-cutting infrastructure in Mêtis.
    It owns shared services such as:

    - quota enforcement
    - audit logging
    - task scheduling and worker execution
    - event infrastructure for the Observer Pattern

    The EventBus is wired here so the rest of the system can depend on a single,
    shared event channel without introducing additional global state.
    """

    def __init__(self):
        # ------------------------------------------------------------------
        # Core operational services
        # ------------------------------------------------------------------
        self.quota = QuotaService()
        self.audit_logger = logging.getLogger("metis.audit")

        self.clock = Clock()
        self.retry_policy = FixedDelayRetryPolicy()

        # ------------------------------------------------------------------
        # Observer Pattern infrastructure
        # ------------------------------------------------------------------
        # The EventBus acts as the central event channel for the application.
        # Core components will publish events to this bus, while observers
        # subscribe independently and react to them.
        self.event_bus = EventBus()

        # Default concrete observers.
        #
        # We keep these as attributes so they are easy to inspect in tests and
        # so other components can access their in-memory state if needed.
        self.logging_observer = LoggingObserver()
        self.metrics_observer = MetricsObserver()
        self.analytics_observer = AnalyticsObserver()
        self.safety_observer = SafetyObserver()

        # Global observers receive all events.
        #
        # This is appropriate for concerns such as:
        # - logging
        # - metrics
        # - broad analytics
        self.event_bus.subscribe_all(self.logging_observer)
        self.event_bus.subscribe_all(self.metrics_observer)
        self.event_bus.subscribe_all(self.analytics_observer)

        # SafetyObserver should focus on higher-signal events rather than every
        # event in the system. We subscribe it selectively so it remains useful
        # and does not become noisy.
        self.event_bus.subscribe("policy.blocked", self.safety_observer)
        self.event_bus.subscribe("response.failed", self.safety_observer)
        self.event_bus.subscribe("command.failed", self.safety_observer)
        self.event_bus.subscribe("model.failed", self.safety_observer)
        self.event_bus.subscribe("task.failed", self.safety_observer)
        self.event_bus.subscribe("task.abandoned", self.safety_observer)

        # ------------------------------------------------------------------
        # Scheduling infrastructure
        # ------------------------------------------------------------------
        scheduler_backend = os.getenv("METIS_TASK_SCHEDULER", "sqlite").lower()
        sqlite_path = Path(os.getenv("METIS_TASK_DB", ".metis/tasks.db"))

        if scheduler_backend == "inmemory":
            self.scheduler = InMemoryTaskScheduler(clock=self.clock)
        else:
            self.scheduler = SQLiteTaskScheduler(db_path=sqlite_path, clock=self.clock)

        self.executor_registry = TaskExecutorRegistry()
        self.executor_registry.register("generic", execute_generic_task)
        self.executor_registry.register("tool_command", execute_tool_task)

        # Pass the shared EventBus into Worker so task lifecycle events are
        # emitted through the same observer infrastructure as request, command,
        # and model events.
        self.worker = Worker(
            scheduler=self.scheduler,
            clock=self.clock,
            retry_policy=self.retry_policy,
            executor_registry=self.executor_registry,
            event_bus=self.event_bus,
        )


_services_singleton = Services()


def get_services() -> Services:
    """
    Return the shared service container.

    Using a singleton here keeps infrastructure consistent across:
    - request handling
    - tool execution
    - scheduled task execution

    That includes the shared EventBus and observer registrations.
    """
    return _services_singleton