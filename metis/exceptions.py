"""
Custom exception definitions for the Metis system.
"""

class ToolExecutionError(Exception):
    """Raised when a tool (e.g. weather API) fails to execute properly."""
    pass