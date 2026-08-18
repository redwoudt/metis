"""Application composition root, including Chapter 17 plugin activation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock
from typing import Any, Iterable, Mapping

from metis.behavior import build_default_behavior_strategy
from metis.events import (
    AnalyticsObserver,
    Event,
    EventBus,
    LoggingObserver,
    MetricsObserver,
    SafetyObserver,
)
from metis.inspection import InspectionService
from metis.models.model_factory import ModelFactory
from metis.plugins import ExtensionRegistries, PluginManager
from metis.scheduling.clock import Clock
from metis.scheduling.executors import TaskExecutorRegistry
from metis.scheduling.retry import FixedDelayRetryPolicy
from metis.scheduling.scheduler import InMemoryTaskScheduler, SQLiteTaskScheduler
from metis.scheduling.worker import Worker
from metis.tools import ToolExecutor


class QuotaService:
    """Extremely small quota and usage tracker for tool execution."""

    def __init__(self, limit_per_user: int = 100):
        self.limit_per_user = limit_per_user
        self.usage: dict[str, int] = {}

    def allow(self, user_id: str, tool_name: str) -> bool:
        count = self.usage.get(user_id, 0)
        if count >= self.limit_per_user:
            return False
        self.usage[user_id] = count + 1
        return True


def execute_generic_task(task: Any, context: Any = None) -> dict[str, Any]:
    return {
        "delivered": True,
        "description": task.description,
        "task_type": task.task_type,
        "payload": dict(task.payload or {}),
    }


class Services:
    """Composition root for built-in and explicitly admitted capabilities."""

    def __init__(
        self,
        *,
        plugin_config: Mapping[str, Any] | None = None,
        plugin_candidates: Iterable[Any] | None = None,
    ) -> None:
        resolved_plugin_config = dict(
            plugin_config if plugin_config is not None else _plugin_config_from_env()
        )

        # Discover and activate before any request-time consumer captures a
        # registry. Entry-point metadata is filtered before plugin code loads.
        self.extension_registries = ExtensionRegistries.with_builtins()
        self.plugin_manager = PluginManager(self.extension_registries)
        self.plugin_report = self.plugin_manager.activate(
            resolved_plugin_config,
            candidates=plugin_candidates,
        )
        self.extension_registries.freeze()

        self.quota = QuotaService()
        self.audit_logger = logging.getLogger("metis.audit")
        self.tool_executor = ToolExecutor(
            services=self,
            commands=self.extension_registries.commands,
        )
        self.model_factory = ModelFactory(self.extension_registries.model_adapters)
        self.inspection_service = InspectionService()
        self.clock = Clock()
        self.retry_policy = FixedDelayRetryPolicy()

        # Built-in observers retain their established identity. Plugin
        # observers are then created from committed registration declarations.
        self.event_bus = EventBus()
        self.logging_observer = LoggingObserver()
        self.metrics_observer = MetricsObserver()
        self.analytics_observer = AnalyticsObserver()
        self.safety_observer = SafetyObserver()
        self.event_bus.subscribe_all(self.logging_observer)
        self.event_bus.subscribe_all(self.metrics_observer)
        self.event_bus.subscribe_all(self.analytics_observer)
        for event_type in (
            "policy.blocked",
            "response.failed",
            "command.failed",
            "model.failed",
            "task.failed",
            "task.abandoned",
        ):
            self.event_bus.subscribe(event_type, self.safety_observer)
        self.plugin_observers = self.extension_registries.attach_observers(
            self.event_bus
        )
        self._publish_plugin_report()

        scheduler_backend = os.getenv("METIS_TASK_SCHEDULER", "sqlite").lower()
        sqlite_path = Path(os.getenv("METIS_TASK_DB", ".metis/tasks.db"))
        self.scheduler: Any
        if scheduler_backend == "inmemory":
            self.scheduler = InMemoryTaskScheduler(clock=self.clock)
        else:
            self.scheduler = SQLiteTaskScheduler(
                db_path=sqlite_path,
                clock=self.clock,
            )

        self.executor_registry = TaskExecutorRegistry()
        self.executor_registry.register("generic", execute_generic_task)
        # Bind deferred tool execution to this composition root.  A worker
        # must not resolve a second process-global Services instance and drift
        # away from the frozen registry that admitted the command.
        self.executor_registry.register("tool_command", self._execute_tool_task)
        self.worker = Worker(
            scheduler=self.scheduler,
            clock=self.clock,
            retry_policy=self.retry_policy,
            executor_registry=self.executor_registry,
            event_bus=self.event_bus,
        )

    def _execute_tool_task(self, task: Any, context: Any = None) -> Any:
        """Execute a scheduled tool through this runtime's ToolExecutor."""
        payload = task.payload or {}
        tool_name = payload.get("tool_name")
        args = payload.get("args", {})
        user = payload.get("user", task.created_by)
        if not tool_name:
            raise ValueError("tool_command task requires 'tool_name' in payload.")
        return self.tool_executor.execute_tool(
            tool_name=tool_name,
            args=args,
            user=user,
            services=self,
            correlation_id=payload.get("correlation_id"),
            idempotency_key=payload.get("idempotency_key") or task.id,
        )

    def build_conversation_mediator(
        self,
        *,
        session_manager: Any,
        policy: Any,
        auth_policy: Any = None,
        strategy: Any = None,
        behavior_strategy: Any = None,
        config: Mapping[str, Any] | None = None,
        request_handler: Any = None,
        memory_manager: Any = None,
        engine_cls: Any = None,
    ) -> Any:
        """Build a mediator from the final frozen runtime registries."""
        from metis.mediator import ConversationMediator

        request_config = dict(config or {})
        if behavior_strategy is None:
            behavior_strategy = build_default_behavior_strategy(
                request_config,
                templates=self.extension_registries.behavior_templates,
            )
        return ConversationMediator(
            session_manager=session_manager,
            policy=policy,
            auth_policy=auth_policy,
            strategy=strategy,
            behavior_strategy=behavior_strategy,
            model_resolver=self.model_factory.resolve,
            config=request_config,
            request_handler=request_handler,
            memory_manager=memory_manager,
            services=self,
            engine_cls=engine_cls,
        )

    def get_request_handler(self, *, config: Mapping[str, Any] | None = None) -> Any:
        """Return a request handler wired through this Services container."""
        handler = getattr(self, "_request_handler", None)
        if handler is None or config is not None:
            from metis.handler.request_handler import RequestHandler

            handler = RequestHandler(
                config=dict(config) if config is not None else None,
                services=self,
            )
            if config is None:
                self._request_handler = handler
        return handler

    def _publish_plugin_report(self) -> None:
        for record in self.plugin_report.records:
            self.event_bus.publish(
                Event.create(
                    event_type=f"plugin.{record.status}",
                    source="PluginManager",
                    correlation_id=f"plugin:{record.plugin_id}",
                    payload={
                        "plugin_id": record.plugin_id,
                        "plugin_version": record.plugin_version,
                        "api_version": record.api_version,
                        "status": record.status,
                        "error_category": record.error_category,
                    },
                    metadata={
                        "distribution": record.distribution,
                        "distribution_version": record.distribution_version,
                    },
                    severity="ERROR" if record.status == "rejected" else "INFO",
                )
            )


def _plugin_config_from_env() -> dict[str, Any]:
    enabled = tuple(
        name.strip()
        for name in os.getenv("METIS_ENABLED_PLUGINS", "").split(",")
        if name.strip()
    )
    strict = os.getenv("METIS_STRICT_PLUGINS", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return {"enabled_plugins": enabled, "strict_plugins": strict}


_services_singleton: Services | None = None
_services_lock = Lock()


def get_services() -> Services:
    """Lazily create the process-level composition root on first use.

    Importing :mod:`metis.services.services` is therefore read-only: it no
    longer reads runtime configuration or creates the default SQLite database.
    Hosts that need explicit lifetime control should construct ``Services`` and
    inject it directly.
    """
    global _services_singleton
    if _services_singleton is None:
        with _services_lock:
            if _services_singleton is None:
                _services_singleton = Services()
    return _services_singleton
