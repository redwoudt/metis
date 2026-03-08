from __future__ import annotations

from typing import Any

from .base import ToolCommand, ToolContext
from metis.scheduling.scheduler import BackgroundCommand, TaskStatus, parse_schedule_time


class ScheduleTaskCommand(ToolCommand):
    """
    Command responsible for creating scheduled background tasks.

    Instead of executing work immediately, this command converts user input
    into a durable BackgroundCommand and registers it with the system
    scheduler. The scheduler later releases the task for execution when the
    scheduled time is reached.

    This keeps request handling lightweight while allowing longer‑running
    or delayed operations to be processed asynchronously by worker processes.
    """

    name = "schedule_task"

    def execute(self, context: ToolContext) -> Any:
        """
        Validate scheduling input, construct a BackgroundCommand, and
        register it with the scheduler.

        Required args:
        - time: when the task should be executed
        - description: human‑readable summary of the task

        Optional args:
        - max_retries: maximum retry attempts for failures
        - tool_name: registered tool command to execute later
        - task_args: arguments for the deferred tool command
        - additional fields for non-tool task payloads

        The scheduler persists the task and worker processes execute it
        when the scheduled time is reached.
        """

        # Extract required scheduling parameters from command arguments.
        time = context.args.get("time")
        description = context.args.get("description")

        if not time or not description:
            raise ValueError("Schedule task requires 'time' and 'description'.")

        # Access shared infrastructure services injected into the ToolContext.
        # These services are provided by the system services container and allow
        # commands to interact with scheduling, time, logging, etc.
        services = context.services
        scheduler = getattr(services, "scheduler", None) if services is not None else None
        clock = getattr(services, "clock", None) if services is not None else None

        if scheduler is None or clock is None:
            raise ValueError("Schedule task requires a scheduler service and clock.")

        now = clock.now()

        # Convert the provided time value into a concrete datetime.
        # This supports several human‑friendly formats such as:
        #   "in 10 minutes", "tomorrow", or ISO timestamps.
        scheduled_for = parse_schedule_time(time, now)

        # Determine retry behavior for the task.
        max_retries = int(context.args.get("max_retries", 3))

        # Support two scheduling modes:
        # 1. A deferred tool command executed later through the normal tool pipeline.
        # 2. A generic background task that simply carries structured payload data.
        tool_name = context.args.get("tool_name")
        task_args = context.args.get("task_args", {})

        if tool_name:
            task_type = "tool_command"
            payload = {
                "tool_name": tool_name,
                "args": task_args,
                "user": context.user,
            }
        else:
            task_type = "generic"
            payload = {
                k: v
                for k, v in context.args.items()
                if k not in {"time", "description", "tool_name", "task_args"}
            }

        # Create the durable task object that will be executed later
        # by the background worker subsystem.
        task = BackgroundCommand(
            description=description,
            scheduled_for=scheduled_for,
            task_type=task_type,
            max_retries=max_retries,
            created_by=context.user,
            payload=payload,
        )

        # Persist the task into the scheduler.
        scheduler.schedule(task)

        # Return confirmation metadata describing the scheduled task.
        return {
            "scheduled": True,
            "task_id": task.id,
            "description": description,
            "time": time,
            "scheduled_for": task.scheduled_for.isoformat(),
            "task_type": task.task_type,
            "status": TaskStatus.SCHEDULED,
        }