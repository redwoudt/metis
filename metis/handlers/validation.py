from metis.commands.base import ToolContext
from .base import ToolHandler


class ValidationHandler(ToolHandler):
    """Ensures required args are provided."""

    def _handle(self, context: ToolContext) -> None:
        missing = [k for k, v in context.args.items() if v is None]
        if missing:
            raise ValueError(f"Missing arguments: {', '.join(missing)}")