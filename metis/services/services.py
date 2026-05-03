import logging
import os
from pathlib import Path

from metis.events import EventBus
from metis.events import (
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
        count = self.usage.get(user_id, 0)
        if count >= self.limit_per_user:
            return False
        self.usage[user_id] = count + 1
        return True


def execute_tool_task(task, context=None):
    """
    Execute a scheduled tool task using the standard RequestHandler tool path.
    """
    payload = task.payload or {}
    tool_name = payload.get("tool_name")
    args = payload.get("args", {})
    user = payload.get("user", task.created_by)

    if not tool_name:
        raise ValueError("tool_command task requires 'tool_name' in payload.")

    services = get_services()

    # Use shared handler instead of constructing directly
    handler = services.get_request_handler(
        config={"vendor": "mock", "model": "stub", "policies": {}}
    )

    return handler.execute_tool(tool_name, args=args, user=user, services=services)


def execute_generic_task(task, context=None):
    return {
        "delivered": True,
        "description": task.description,
        "task_type": task.task_type,
        "payload": dict(task.payload or {}),
    }


class Services:
    """
    Composition root for cross-cutting infrastructure in Mêtis.
    """

    def __init__(self):
        # ------------------------------------------------------------------
        # Core services
        # ------------------------------------------------------------------
        self.quota = QuotaService()
        self.audit_logger = logging.getLogger("metis.audit")

        self.clock = Clock()
        self.retry_policy = FixedDelayRetryPolicy()

        # ------------------------------------------------------------------
        # Observer infrastructure
        # ------------------------------------------------------------------
        self.event_bus = EventBus()

        self.logging_observer = LoggingObserver()
        self.metrics_observer = MetricsObserver()
        self.analytics_observer = AnalyticsObserver()
        self.safety_observer = SafetyObserver()

        self.event_bus.subscribe_all(self.logging_observer)
        self.event_bus.subscribe_all(self.metrics_observer)
        self.event_bus.subscribe_all(self.analytics_observer)

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

        self.worker = Worker(
            scheduler=self.scheduler,
            clock=self.clock,
            retry_policy=self.retry_policy,
            executor_registry=self.executor_registry,
            event_bus=self.event_bus,
        )

    # ------------------------------------------------------------------
    # Mediator / Request flow wiring
    # ------------------------------------------------------------------
    def build_conversation_mediator(
        self,
        *,
        session_manager,
        policy,
        auth_policy=None,
        strategy=None,
        config=None,
        request_handler=None,
        engine_cls=None,
    ):
        """
        Build a ConversationMediator using this Services container.

        Lazy import avoids circular dependencies.
        """
        from metis.mediator import ConversationMediator

        return ConversationMediator(
            session_manager=session_manager,
            policy=policy,
            auth_policy=auth_policy,
            strategy=strategy,
            config=config,
            request_handler=request_handler,
            services=self,
            engine_cls=engine_cls,
        )

    def get_request_handler(self, *, config=None):
        """
        Return a RequestHandler wired through this Services container.
        """
        handler = getattr(self, "_request_handler", None)

        if handler is None or config is not None:
            from metis.handler.request_handler import RequestHandler

            handler = RequestHandler(
                config=config,
                services=self,
            )

            if config is None:
                self._request_handler = handler

        return handler


_services_singleton = Services()


def get_services() -> Services:
    return _services_singleton