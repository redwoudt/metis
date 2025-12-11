"""
DEPRECATED — tools/tool_executor.py

ExecutingState previously used this dummy executor to simulate local tool
actions. The system has now migrated to the Command + Chain of Responsibility
architecture, and all tool execution should flow through:

    RequestHandler.execute_tool()

This file is retained only to prevent import errors during transition.
"""

import logging

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Deprecated compatibility shim."""

    def __init__(self, *args, **kwargs):
        logger.warning(
            "tools.ToolExecutor is deprecated. Use RequestHandler.execute_tool() instead."
        )
        raise RuntimeError(
            "ToolExecutor is deprecated. Use RequestHandler.execute_tool() instead."
        )

    def run(self, *args, **kwargs):
        raise RuntimeError(
            "tools.ToolExecutor.run() is no longer supported. "
            "Tool execution must go through RequestHandler.execute_tool()."
        )