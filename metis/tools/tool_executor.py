from typing import Any

from metis.commands import command_registry
from metis.commands.base import ToolContext
from metis.exceptions import ToolExecutionError
from metis.handlers.pipelines import build_light_pipeline, build_strict_pipeline


class ToolExecutor:
    """
    Executes tool commands through the Command + Chain of Responsibility pipeline.

    This class extracts tool execution out of RequestHandler so the handler can
    remain a thin façade and tool execution can be reused by states, scheduled
    tasks, and other orchestration layers.
    """

    def __init__(self, services: Any = None):
        self.services = services

    def execute_tool(self, tool_name, args=None, user=None, services=None):
        if tool_name not in command_registry:
            raise ToolExecutionError(f"Unknown tool '{tool_name}'")

        command = command_registry[tool_name]()
        services = services or self.services or self._get_services()
        safe_args = dict(args or {})

        if user is None:
            user = safe_args.get("user")
        if user is not None and "user" not in safe_args:
            safe_args["user"] = user

        context = ToolContext(
            command=command,
            args=safe_args,
            user=user,
            metadata={"allow_user_tools": True},
            services=services,
        )

        if tool_name in {"execute_sql", "schedule_task"} and services is not None:
            pipeline = build_strict_pipeline(
                services.quota,
                services.audit_logger,
            )
        else:
            pipeline = build_light_pipeline()

        return pipeline.handle(context).result

    def execute(self, tool_name, args=None, user=None, services=None):
        """
        Convenience alias for callers that prefer a shorter method name.
        """
        return self.execute_tool(
            tool_name=tool_name,
            args=args,
            user=user,
            services=services,
        )

    def _get_services(self):
        """
        Lazily resolve services to avoid circular imports during Config startup.
        """
        from metis.config import Config

        return Config.services()