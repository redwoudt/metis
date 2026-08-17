"""Strategies that resolve one coherent behavior plan per request."""

from typing import Mapping, Protocol

from .plans import BehaviorContext, BehaviorPlan


class BehaviorStrategy(Protocol):
    def choose(self, context: BehaviorContext) -> BehaviorPlan: ...


class TemplateBehaviorStrategy:
    """Resolve a named immutable template using explicit precedence."""

    def __init__(
        self,
        templates: Mapping[str, BehaviorPlan],
        default_name: str = "balanced",
    ):
        self._templates = dict(templates)
        if default_name not in self._templates:
            raise ValueError(f"Unknown default behavior template: {default_name}")
        self._default_name = default_name

    def choose(self, context: BehaviorContext) -> BehaviorPlan:
        name = (
            (
                context.requested_template
                or context.configured_default
                or self._default_name
            )
            .strip()
            .lower()
        )
        try:
            return self._templates[name]
        except KeyError as exc:
            raise ValueError(f"Unknown behavior template: {name}") from exc


class RiskAwareBehaviorStrategy:
    """Override ordinary selection when a request requires stricter behavior."""

    def __init__(self, base: BehaviorStrategy, safety_plan: BehaviorPlan):
        self._base = base
        self._safety_plan = safety_plan

    def choose(self, context: BehaviorContext) -> BehaviorPlan:
        if context.risk.strip().lower() == "high":
            return self._safety_plan
        return self._base.choose(context)
