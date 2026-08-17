"""Constrained, staged registration for plugin contributions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING

from metis.behavior import BehaviorPlan

from .contracts import PluginMetadata
from .errors import PluginContractError, PluginConflictError

if TYPE_CHECKING:  # pragma: no cover
    from .registries import ExtensionRegistries


Factory = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class ObserverContribution:
    """One observer factory and the event stream it should receive."""

    plugin_id: str
    event_type: str
    factory: Factory


@dataclass(slots=True)
class RegistrationBatch:
    """All declarations made by one plugin before atomic commit."""

    metadata: PluginMetadata
    commands: dict[str, Factory] = field(default_factory=dict)
    behavior_templates: dict[str, BehaviorPlan] = field(default_factory=dict)
    model_adapters: dict[str, Factory] = field(default_factory=dict)
    observers: list[ObserverContribution] = field(default_factory=list)

    @property
    def contribution_count(self) -> int:
        return (
            len(self.commands)
            + len(self.behavior_templates)
            + len(self.model_adapters)
            + len(self.observers)
        )


class PluginRegistrar:
    """Facade exposing only extension points supported by the host."""

    def __init__(
        self,
        metadata: PluginMetadata,
        registries: "ExtensionRegistries",
    ) -> None:
        self._metadata = metadata
        self._registries = registries
        self._batch = RegistrationBatch(metadata=metadata)
        self._open = True

    @property
    def batch(self) -> RegistrationBatch:
        return self._batch

    def command(self, name: str, factory: Factory) -> None:
        """Register a namespaced factory producing a ``ToolCommand``."""
        self._require_open()
        key = self._contribution_name(name)
        self._require_factory(factory, "command")
        if key in self._batch.commands:
            raise PluginConflictError(f"Command '{key}' was declared more than once")
        self._batch.commands[key] = factory

    def behavior_template(self, plan: BehaviorPlan) -> None:
        """Register one immutable, namespaced behaviour plan."""
        self._require_open()
        if not isinstance(plan, BehaviorPlan):
            raise PluginContractError(
                "behavior_template() expects an immutable BehaviorPlan"
            )
        key = self._contribution_name(plan.name)
        if key in self._batch.behavior_templates:
            raise PluginConflictError(
                f"Behavior template '{key}' was declared more than once"
            )
        self._batch.behavior_templates[key] = plan

    def model_adapter(self, vendor: str, factory: Factory) -> None:
        """Register a namespaced model-adapter factory."""
        self._require_open()
        key = self._contribution_name(vendor)
        self._require_factory(factory, "model adapter")
        if key in self._batch.model_adapters:
            raise PluginConflictError(
                f"Model adapter '{key}' was declared more than once"
            )
        self._batch.model_adapters[key] = factory

    def observer(self, event_type: str, factory: Factory) -> None:
        """Register an observer factory for one event type or ``*``."""
        self._require_open()
        event_name = str(event_type).strip()
        if not event_name:
            raise PluginContractError("Observer event_type cannot be empty")
        self._require_factory(factory, "observer")
        contribution = ObserverContribution(
            plugin_id=self._metadata.plugin_id,
            event_type=event_name,
            factory=factory,
        )
        if contribution in self._batch.observers:
            raise PluginConflictError(
                f"Observer for '{event_name}' was declared more than once"
            )
        self._batch.observers.append(contribution)

    def validate(self) -> None:
        """Validate the completed batch without changing live registries."""
        self._require_open()
        self._registries.validate_batch(self._batch)

    def _contribution_name(self, name: str) -> str:
        value = str(name).strip().lower()
        prefix = f"{self._metadata.plugin_id}."
        if not value.startswith(prefix) or value == prefix:
            raise PluginContractError(
                f"External contribution '{value}' must use the '{prefix}' namespace"
            )
        return value

    @staticmethod
    def _require_factory(factory: Factory, contribution_type: str) -> None:
        if not callable(factory):
            raise PluginContractError(
                f"The {contribution_type} contribution must be callable"
            )

    def _require_open(self) -> None:
        if not self._open:
            raise PluginContractError("The registration window has closed")

    def _close(self) -> None:
        self._open = False
