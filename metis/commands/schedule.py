from typing import Any
from .base import ToolCommand, ToolContext


class ScheduleTaskCommand(ToolCommand):
    name = "schedule_task"

    def execute(self, context: ToolContext) -> Any:
        time = context.args.get("time")
        description = context.args.get("description")

        if not time or not description:
            raise ValueError("Schedule task requires 'time' and 'description'.")

        # Replace with actual scheduling logic
        return {"scheduled": True, "time": time, "description": description}