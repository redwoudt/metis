"""
tool_executor.py — Deprecated.

This class previously performed direct tool execution, but the system
has fully migrated to the new Command + Chain of Responsibility architecture.

ToolExecutor now remains ONLY as a compatibility stub to avoid breaking imports.
All callers should route tool execution through:

    RequestHandler.execute_tool()

This file may be safely deleted once all legacy references are removed.
"""

import logging

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    DEPRECATED.

    Retained only to prevent import errors during the migration.
    It does nothing and should not be used for real tool execution.
    """

    def __init__(self, *args, **kwargs):
        logger.warning(
            "ToolExecutor is deprecated and no longer performs tool execution. "
            "Use RequestHandler.execute_tool() instead."
        )
        raise RuntimeError(
            "ToolExecutor is deprecated. Use RequestHandler.execute_tool() instead."
        )

    def execute(self, *args, **kwargs):
        raise RuntimeError(
            "ToolExecutor.execute() has been removed. "
            "Use RequestHandler.execute_tool() instead."
        )