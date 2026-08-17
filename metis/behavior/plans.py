"""Immutable inputs and outputs for system behavior selection."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorContext:
    requested_template: str | None = None
    configured_default: str | None = None
    risk: str = "normal"


@dataclass(frozen=True)
class BehaviorPlan:
    name: str
    model_role: str
    response_style: str
    allow_tools: bool
    require_safety: bool
    include_citations: bool = False
