"""Versioned plugin host for independently distributed Mêtis capabilities."""

from .contracts import MetisPlugin, PluginMetadata
from .discovery import PLUGIN_ENTRY_POINT_GROUP, discover_plugins
from .errors import (
    PluginActivationError,
    PluginConflictError,
    PluginContractError,
    PluginError,
    RegistryFrozenError,
)
from .manager import PluginLoadRecord, PluginLoadReport, PluginManager
from .registrar import PluginRegistrar
from .registries import ExtensionRegistries

__all__ = [
    "ExtensionRegistries",
    "MetisPlugin",
    "PLUGIN_ENTRY_POINT_GROUP",
    "PluginActivationError",
    "PluginConflictError",
    "PluginContractError",
    "PluginError",
    "PluginLoadRecord",
    "PluginLoadReport",
    "PluginManager",
    "PluginMetadata",
    "PluginRegistrar",
    "RegistryFrozenError",
    "discover_plugins",
]
