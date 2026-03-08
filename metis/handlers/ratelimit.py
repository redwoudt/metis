from metis.commands.base import ToolContext
from .base import ToolHandler


class RateLimitHandler(ToolHandler):
    """
    Handler that enforces quota limits before command execution.

    The handler accepts either a rich user object with an `id` attribute or a
    plain user identifier string. This keeps the quota check compatible with
    both application flows and lightweight tests.
    """

    def __init__(self, quota_service, next_handler=None):
        super().__init__(next_handler)
        self.quota = quota_service

    def _handle(self, context: ToolContext) -> None:
        """
        Extract a usable user identifier and verify that command execution is
        still allowed under the current quota policy.
        """
        user = context.user

        # Support both:
        # - rich user objects with an `.id` attribute
        # - plain string identifiers used in simpler flows or tests
        user_id = getattr(user, "id", user)

        if not self.quota.allow(user_id, context.command.name):
            raise RuntimeError(f"Rate limit exceeded for {context.command.name}.")