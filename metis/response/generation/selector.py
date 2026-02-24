"""
Strategy Selector

Responsible for choosing the correct generation strategy
based on DSL context and system configuration.

Precedence:
    1. DSL tag (highest priority)
    2. Config default
    3. System default
"""

from typing import Any, Mapping
from .base import ResponseGenerationStrategy
from .strategies import (
    DefaultStrategy,
    ConciseStrategy,
    DetailedStrategy,
    CreativeStrategy,
    AnalyticalStrategy
)

# Registry mapping string style → strategy instance
_MAP = {
    "default": DefaultStrategy(),
    "concise": ConciseStrategy(),
    "detailed": DetailedStrategy(),
    "creative": CreativeStrategy(),
    "analytical": AnalyticalStrategy(),
}


class StrategySelector:
    """
    Selects the appropriate generation strategy.
    """

    def select(
        self,
        dsl_ctx: dict[str, Any],
        config: Mapping[str, Any]
    ) -> ResponseGenerationStrategy:
        """
        Determine strategy from DSL and config.

        Parameters:
            dsl_ctx: DSL interpreter context
            config: system configuration

        Returns:
            ResponseGenerationStrategy
        """

        # DSL override
        style = (
            dsl_ctx.get("style")
            or dsl_ctx.get("response_style")
            or ""
        ).strip().lower()

        if style in _MAP:
            return _MAP[style]

        # Config fallback
        cfg_style = str(config.get("response_style", "")).strip().lower()
        if cfg_style in _MAP:
            return _MAP[cfg_style]

        # Safe default
        return _MAP["default"]