from dataclasses import FrozenInstanceError

import pytest

from metis.behavior import (
    BehaviorContext,
    BehaviorStrategy,
    DEFAULT_TEMPLATES,
    RiskAwareBehaviorStrategy,
    TemplateBehaviorStrategy,
)


def make_strategy() -> BehaviorStrategy:
    base = TemplateBehaviorStrategy(DEFAULT_TEMPLATES, "balanced")
    return RiskAwareBehaviorStrategy(base, DEFAULT_TEMPLATES["safety-first"])


def test_request_template_overrides_configured_default() -> None:
    plan = make_strategy().choose(
        BehaviorContext(
            requested_template="creative",
            configured_default="balanced",
        )
    )
    assert plan.name == "creative"
    assert plan.model_role == "creative"


def test_high_risk_request_uses_safety_first_template() -> None:
    plan = make_strategy().choose(
        BehaviorContext(requested_template="creative", risk="high")
    )
    assert plan.name == "safety-first"
    assert plan.allow_tools is False
    assert plan.require_safety is True


def test_unknown_template_fails_clearly() -> None:
    with pytest.raises(ValueError, match="Unknown behavior template"):
        make_strategy().choose(BehaviorContext(requested_template="fast-ish"))


def test_configured_template_overrides_code_default() -> None:
    plan = make_strategy().choose(BehaviorContext(configured_default="creative"))
    assert plan.name == "creative"


def test_behavior_plans_are_immutable() -> None:
    plan = make_strategy().choose(BehaviorContext())
    with pytest.raises(FrozenInstanceError):
        plan.allow_tools = False  # type: ignore[misc]
