from metis.commands.base import ToolContext
from .base import ToolHandler


class RateLimitHandler(ToolHandler):
    def __init__(self, quota_service, next_handler=None):
        super().__init__(next_handler)
        self.quota = quota_service

    def _handle(self, context: ToolContext) -> None:
        if not self.quota.allow(context.user.id, context.command.name):
            raise RuntimeError(f"Rate limit exceeded for {context.command.name}.")