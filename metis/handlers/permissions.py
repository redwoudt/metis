from metis.commands.base import ToolContext
from .base import ToolHandler


class PermissionHandler(ToolHandler):
    def _handle(self, context: ToolContext) -> None:
        allowed = context.metadata.get("allow_user_tools", False)
        if not allowed and context.user.role != "admin":
            raise PermissionError(f"User not allowed to execute {context.command.name}.")