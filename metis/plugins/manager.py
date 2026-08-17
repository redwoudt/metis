"""Admission, validation, activation, and reporting for Mêtis plugins."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .contracts import MetisPlugin, PluginMetadata
from .discovery import discover_plugins
from .errors import (
    PluginActivationError,
    PluginConflictError,
    PluginContractError,
    RegistryFrozenError,
)
from .registries import ExtensionRegistries


@dataclass(frozen=True, slots=True)
class PluginLoadRecord:
    """One immutable discovery or activation outcome."""

    plugin_id: str
    status: str
    distribution: str = "unknown"
    distribution_version: str = "unknown"
    plugin_version: str | None = None
    api_version: str | None = None
    error_category: str | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class PluginLoadReport:
    """Complete deterministic result of one activation pass."""

    records: tuple[PluginLoadRecord, ...]

    @property
    def loaded(self) -> tuple[PluginLoadRecord, ...]:
        return tuple(record for record in self.records if record.status == "loaded")

    @property
    def rejected(self) -> tuple[PluginLoadRecord, ...]:
        return tuple(record for record in self.records if record.status == "rejected")

    @property
    def disabled(self) -> tuple[PluginLoadRecord, ...]:
        return tuple(record for record in self.records if record.status == "disabled")


class PluginManager:
    """Own the plugin lifecycle during application assembly."""

    def __init__(
        self,
        registries: ExtensionRegistries,
        *,
        supported_api_versions: Iterable[str] = ("1",),
    ) -> None:
        self._registries = registries
        self._supported_api_versions = frozenset(
            str(version) for version in supported_api_versions
        )
        self._activated = False
        self._report: PluginLoadReport | None = None
        self._strict_failure = False

    def activate(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        candidates: Iterable[Any] | None = None,
    ) -> PluginLoadReport:
        """Discover broadly, admit enabled names, and activate each plugin once."""
        if self._activated:
            assert self._report is not None
            if self._strict_failure:
                raise PluginActivationError(
                    "Strict plugin activation previously failed",
                    self._report,
                )
            return self._report

        settings = dict(config or {})
        enabled = _normalise_enabled(settings.get("enabled_plugins", ()))
        strict = bool(settings.get("strict_plugins", False))
        entries = tuple(candidates) if candidates is not None else discover_plugins()
        entries = tuple(sorted(entries, key=_entry_point_sort_key))
        counts = Counter(str(entry.name) for entry in entries)
        records: list[PluginLoadRecord] = []

        discovered_names = {str(entry.name) for entry in entries}
        for missing in sorted(enabled.difference(discovered_names)):
            records.append(
                PluginLoadRecord(
                    plugin_id=missing,
                    status="rejected",
                    error_category="not-installed",
                    message=f"Enabled plugin '{missing}' is not installed",
                )
            )

        for entry_point in entries:
            name = str(entry_point.name)
            distribution, distribution_version = _distribution_identity(entry_point)

            if counts[name] > 1:
                records.append(
                    PluginLoadRecord(
                        plugin_id=name,
                        status="rejected",
                        distribution=distribution,
                        distribution_version=distribution_version,
                        error_category="duplicate-entry-point",
                        message=f"More than one distribution advertises '{name}'",
                    )
                )
                continue

            if name not in enabled:
                records.append(
                    PluginLoadRecord(
                        plugin_id=name,
                        status="disabled",
                        distribution=distribution,
                        distribution_version=distribution_version,
                        message="Installed but not enabled",
                    )
                )
                continue

            records.append(
                self._activate_one(
                    entry_point,
                    distribution=distribution,
                    distribution_version=distribution_version,
                )
            )

        report = PluginLoadReport(records=tuple(records))
        self._report = report
        self._activated = True
        enabled_rejections = [
            record for record in report.rejected if record.plugin_id in enabled
        ]
        if strict and enabled_rejections:
            self._strict_failure = True
            failed = ", ".join(
                sorted({record.plugin_id for record in enabled_rejections})
            )
            raise PluginActivationError(
                f"Required plugin activation failed: {failed}",
                report,
            )
        return report

    def _activate_one(
        self,
        entry_point: Any,
        *,
        distribution: str,
        distribution_version: str,
    ) -> PluginLoadRecord:
        name = str(entry_point.name)
        metadata: PluginMetadata | None = None
        phase = "load"
        try:
            plugin = entry_point.load()
            if isinstance(plugin, type):
                plugin = plugin()
            phase = "contract"
            if not isinstance(plugin, MetisPlugin):
                raise PluginContractError(
                    "Entry point must expose an object with metadata and register()"
                )
            metadata = plugin.metadata
            if not isinstance(metadata, PluginMetadata):
                raise PluginContractError(
                    "Plugin metadata must be a PluginMetadata instance"
                )
            if metadata.plugin_id != name:
                raise PluginContractError(
                    f"Plugin ID '{metadata.plugin_id}' does not match entry-point "
                    f"name '{name}'"
                )
            if metadata.api_version not in self._supported_api_versions:
                raise PluginContractError(
                    f"Unsupported plugin API version '{metadata.api_version}'"
                )

            phase = "registration"
            with self._registries.stage(metadata) as registrar:
                plugin.register(registrar)

            return PluginLoadRecord(
                plugin_id=name,
                status="loaded",
                distribution=distribution,
                distribution_version=distribution_version,
                plugin_version=metadata.version,
                api_version=metadata.api_version,
            )
        except Exception as exc:
            return PluginLoadRecord(
                plugin_id=name,
                status="rejected",
                distribution=distribution,
                distribution_version=distribution_version,
                plugin_version=metadata.version if metadata else None,
                api_version=metadata.api_version if metadata else None,
                error_category=_error_category(exc, phase),
                message=str(exc),
            )


def _normalise_enabled(value: Any) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        items = value.split(",")
    else:
        items = value
    return frozenset(str(item).strip() for item in items if str(item).strip())


def _distribution_identity(entry_point: Any) -> tuple[str, str]:
    distribution = getattr(entry_point, "dist", None)
    return (
        str(getattr(distribution, "name", "unknown")),
        str(getattr(distribution, "version", "unknown")),
    )


def _entry_point_sort_key(entry_point: Any) -> tuple[str, str, str]:
    distribution, _ = _distribution_identity(entry_point)
    return (
        str(entry_point.name),
        distribution,
        str(getattr(entry_point, "value", "")),
    )


def _error_category(exc: Exception, phase: str) -> str:
    if isinstance(exc, PluginConflictError):
        return "conflict"
    if isinstance(exc, PluginContractError):
        return "contract"
    if isinstance(exc, RegistryFrozenError):
        return "lifecycle"
    return f"{phase}-error"
