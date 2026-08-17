"""Built-in named behavior templates and default composition."""

from typing import Any, Mapping

from .plans import BehaviorPlan
from .strategies import (
    BehaviorStrategy,
    RiskAwareBehaviorStrategy,
    TemplateBehaviorStrategy,
)


DEFAULT_TEMPLATES = {
    "balanced": BehaviorPlan(
        name="balanced",
        model_role="analysis",
        response_style="default",
        allow_tools=True,
        require_safety=True,
    ),
    "creative": BehaviorPlan(
        name="creative",
        model_role="creative",
        response_style="creative",
        allow_tools=True,
        require_safety=True,
    ),
    "safety-first": BehaviorPlan(
        name="safety-first",
        model_role="analysis",
        response_style="analytical",
        allow_tools=False,
        require_safety=True,
        include_citations=True,
    ),
}


def build_default_behavior_strategy(
    config: Mapping[str, Any],
    templates: Mapping[str, BehaviorPlan] | None = None,
) -> BehaviorStrategy:
    available = dict(templates or DEFAULT_TEMPLATES)
    configured = str(config.get("behavior_template") or "balanced").strip().lower()
    base = TemplateBehaviorStrategy(available, default_name=configured)
    try:
        safety_plan = available["safety-first"]
    except KeyError as exc:
        raise ValueError("Behavior templates must retain 'safety-first'") from exc
    return RiskAwareBehaviorStrategy(base, safety_plan)
