from metis.commands.base import ToolContext
from .base import ToolHandler


class AuditLogHandler(ToolHandler):
    def __init__(self, logger, next_handler=None):
        super().__init__(next_handler)
        self.logger = logger

    def _handle(self, context: ToolContext) -> None:
        self.logger.info(f"Executing tool: {context.command.name}")