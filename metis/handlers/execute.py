from metis.commands.base import ToolContext
from .base import ToolHandler


class ExecuteCommandHandler(ToolHandler):
    """Final handlers that performs the action."""

    def _handle(self, context: ToolContext) -> None:
        context.result = context.command.execute(context)