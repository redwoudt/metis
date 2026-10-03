from types import SimpleNamespace
from typing import Any

import pytest

from metis.behavior import DEFAULT_TEMPLATES
from metis.mediator import ConversationMediator, RequestContext
from metis.response.generation.strategies import (
    AnalyticalStrategy,
    CreativeStrategy,
    DefaultStrategy,
)


def make_mediator(**config: Any) -> ConversationMediator:
    return ConversationMediator(
        config={
            "vendor": "mock",
            "model": "stub",
            "policies": {},
            **config,
        }
    )


def make_context(dsl_context: dict[str, Any], plan_name: str) -> RequestContext:
    context = RequestContext(user_id="reader", user_input="test")
    context.dsl_context = dsl_context
    context.behavior_plan = DEFAULT_TEMPLATES[plan_name]
    context.engine = SimpleNamespace(
        preferences={},
        response_strategy=None,
    )
    return context


def test_implicit_balanced_preserves_earlier_role_and_style() -> None:
    mediator = make_mediator()
    mediator.model_resolver = lambda *_: object()
    context = make_context(
        {"task": "creative", "style": "creative"},
        "balanced",
    )

    mediator.select_model(context)
    mediator.configure_response_strategy(context)

    assert context.model_role == "creative"
    assert isinstance(context.engine.response_strategy, CreativeStrategy)


def test_explicit_balanced_applies_plan_role_and_style() -> None:
    mediator = make_mediator()
    mediator.model_resolver = lambda *_: object()
    context = make_context(
        {
            "behavior": "balanced",
            "task": "creative",
            "style": "creative",
        },
        "balanced",
    )

    mediator.select_model(context)
    mediator.configure_response_strategy(context)

    assert context.model_role == "analysis"
    assert isinstance(context.engine.response_strategy, DefaultStrategy)


def test_explicit_behavior_template_controls_response_style() -> None:
    mediator = make_mediator()
    context = make_context(
        {"behavior": "safety-first", "style": "creative"},
        "safety-first",
    )

    mediator.configure_response_strategy(context)

    assert isinstance(context.engine.response_strategy, AnalyticalStrategy)


def test_safety_first_plan_denies_requested_tools() -> None:
    mediator = make_mediator()
    context = make_context({"tool": "search_web"}, "safety-first")

    with pytest.raises(PermissionError, match="does not allow tool execution"):
        mediator.select_tool(context)


def test_plan_safeguards_cannot_be_weakened_by_request_flags() -> None:
    mediator = make_mediator()
    context = make_context(
        {
            "safety_enabled": False,
            "include_citations": False,
        },
        "safety-first",
    )

    mediator.apply_rendering_preferences(context)

    assert context.engine.preferences["safety_enabled"] is True
    assert context.engine.preferences["include_citations"] is True


def test_high_risk_task_overrides_requested_creative_template() -> None:
    mediator = make_mediator()
    context = RequestContext(user_id="reader", user_input="test")
    context.dsl_context = {
        "behavior": "creative",
        "task": "medical",
    }

    mediator.resolve_behavior(context)

    assert context.behavior_plan == DEFAULT_TEMPLATES["safety-first"]
