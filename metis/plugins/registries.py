"""Typed extension registries with atomic staging and freeze semantics."""

from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from types import MappingProxyType
from typing import Any, Iterator, Mapping

from metis.behavior import BehaviorPlan, DEFAULT_TEMPLATES
from metis.commands import command_registry
from metis.events import Observer
from metis.models.model_factory import default_adapter_factories
from metis.response.generation.selector import available_response_styles

from .contracts import PluginMetadata
from .errors import (
    PluginConflictError,
    PluginContractError,
    RegistryFrozenError,
)
from .registrar import ObserverContribution, PluginRegistrar, RegistrationBatch


class ExtensionRegistries:
    """Own all public plugin extension points during application assembly."""

    def __init__(
        self,
        *,
        commands: Mapping[str, Any],
        behavior_templates: Mapping[str, BehaviorPlan],
        model_adapters: Mapping[str, Any],
        known_model_roles: set[str],
        known_response_styles: set[str],
    ) -> None:
        self._commands = dict(commands)
        self._behavior_templates = dict(behavior_templates)
        self._model_adapters = dict(model_adapters)
        self._observers: list[ObserverContribution] = []
        self._known_model_roles = set(known_model_roles)
        self._known_response_styles = set(known_response_styles)
        self._owners: dict[str, dict[str, str]] = {
            "command": {name: "metis" for name in self._commands},
            "behavior_template": {name: "metis" for name in self._behavior_templates},
            "model_adapter": {name: "metis" for name in self._model_adapters},
        }
        self._frozen = False
        self._lock = RLock()

    @classmethod
    def with_builtins(cls) -> "ExtensionRegistries":
        """Create registries seeded with every capability in the snapshot."""
        from metis.config import Config

        roles = set(getattr(Config, "MODEL_REGISTRY", {}))
        roles.update(plan.model_role for plan in DEFAULT_TEMPLATES.values())
        return cls(
            commands=command_registry,
            behavior_templates=DEFAULT_TEMPLATES,
            model_adapters=default_adapter_factories(),
            known_model_roles=roles,
            known_response_styles=set(available_response_styles()),
        )

    @property
    def commands(self) -> Mapping[str, Any]:
        return MappingProxyType(self._commands)

    @property
    def behavior_templates(self) -> Mapping[str, BehaviorPlan]:
        return MappingProxyType(self._behavior_templates)

    @property
    def model_adapters(self) -> Mapping[str, Any]:
        return MappingProxyType(self._model_adapters)

    @property
    def observer_contributions(self) -> tuple[ObserverContribution, ...]:
        return tuple(self._observers)

    @property
    def frozen(self) -> bool:
        return self._frozen

    @contextmanager
    def stage(self, metadata: PluginMetadata) -> Iterator[PluginRegistrar]:
        """Commit one plugin's declarations only when every check succeeds."""
        self._require_mutable()
        registrar = PluginRegistrar(metadata, self)
        try:
            yield registrar
            registrar.validate()
            self._commit(registrar.batch)
        finally:
            registrar._close()

    def validate_batch(self, batch: RegistrationBatch) -> None:
        """Validate a proposed batch against the complete live state."""
        with self._lock:
            self._require_mutable()
            if batch.contribution_count == 0:
                raise PluginContractError(
                    f"Plugin '{batch.metadata.plugin_id}' registered no contributions"
                )

            self._reject_collisions("command", batch.commands, self._commands)
            self._reject_collisions(
                "behavior template",
                batch.behavior_templates,
                self._behavior_templates,
            )
            self._reject_collisions(
                "model adapter",
                batch.model_adapters,
                self._model_adapters,
            )

            for plan in batch.behavior_templates.values():
                if plan.model_role not in self._known_model_roles:
                    raise PluginContractError(
                        f"Behavior template '{plan.name}' references unknown "
                        f"model role '{plan.model_role}'"
                    )
                if plan.response_style not in self._known_response_styles:
                    raise PluginContractError(
                        f"Behavior template '{plan.name}' references unknown "
                        f"response style '{plan.response_style}'"
                    )

    def freeze(self) -> None:
        """Close every registry before request handling begins."""
        with self._lock:
            self._frozen = True

    def attach_observers(self, event_bus: Any) -> tuple[Observer, ...]:
        """Create and attach all contributed observers after activation."""
        attached: list[Observer] = []
        for contribution in self._observers:
            observer = contribution.factory()
            if not isinstance(observer, Observer):
                raise PluginContractError(
                    f"Observer factory from '{contribution.plugin_id}' did not "
                    "return an object implementing notify(event)"
                )
            if contribution.event_type == "*":
                event_bus.subscribe_all(observer)
            else:
                event_bus.subscribe(contribution.event_type, observer)
            attached.append(observer)
        return tuple(attached)

    def owner_of(self, contribution_type: str, name: str) -> str | None:
        """Return the plugin ID responsible for a named contribution."""
        return self._owners.get(contribution_type, {}).get(name)

    def _commit(self, batch: RegistrationBatch) -> None:
        with self._lock:
            self.validate_batch(batch)
            owner = batch.metadata.plugin_id
            self._commands.update(batch.commands)
            self._behavior_templates.update(batch.behavior_templates)
            self._model_adapters.update(batch.model_adapters)
            self._observers.extend(batch.observers)
            self._owners["command"].update({name: owner for name in batch.commands})
            self._owners["behavior_template"].update(
                {name: owner for name in batch.behavior_templates}
            )
            self._owners["model_adapter"].update(
                {name: owner for name in batch.model_adapters}
            )

    @staticmethod
    def _reject_collisions(
        contribution_type: str,
        proposed: Mapping[str, Any],
        current: Mapping[str, Any],
    ) -> None:
        collisions = sorted(set(proposed).intersection(current))
        if collisions:
            joined = ", ".join(collisions)
            raise PluginConflictError(
                f"The {contribution_type} name(s) already exist: {joined}"
            )

    def _require_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError("Extension registries are frozen")
