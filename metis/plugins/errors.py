"""Exceptions raised by the Mêtis plugin host."""

from __future__ import annotations

from typing import Any


class PluginError(RuntimeError):
    """Base class for plugin discovery and activation failures."""


class PluginContractError(PluginError):
    """A plugin or one of its declarations violates the public contract."""


class PluginConflictError(PluginContractError):
    """A contribution collides with a built-in or another plugin."""


class RegistryFrozenError(PluginError):
    """A registry mutation was attempted after application assembly."""


class PluginActivationError(PluginError):
    """Strict activation failed; ``report`` contains the complete outcome."""

    def __init__(self, message: str, report: Any):
        super().__init__(message)
        self.report = report
