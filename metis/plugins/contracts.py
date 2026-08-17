"""Public contracts implemented by separately distributed Mêtis plugins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Stable plugin identity and compatibility metadata."""

    plugin_id: str
    version: str
    api_version: str = "1"

    def __post_init__(self) -> None:
        for field_name in ("plugin_id", "version", "api_version"):
            value = str(getattr(self, field_name)).strip()
            if not value:
                raise ValueError(
                    f"Plugin metadata field '{field_name}' cannot be empty"
                )
            object.__setattr__(self, field_name, value)


@runtime_checkable
class MetisPlugin(Protocol):
    """The complete host-facing surface of a Mêtis plugin."""

    metadata: PluginMetadata

    def register(self, registrar: "PluginRegistrar") -> None:
        """Declare contributions through the host-supplied registrar."""
        ...


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported only by static type checkers
    from .registrar import PluginRegistrar
