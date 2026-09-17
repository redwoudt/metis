

"""Authoritative mapping from DSL keys to expression classes."""

from collections.abc import KeysView
from typing import Dict, Optional, Type

from .ast import (
    ArgsExpr,
    BehaviorExpr,
    Expression,
    FormatExpr,
    FormatMarkdownExpr,
    IncludeCitationsExpr,
    LengthExpr,
    PersonaExpr,
    SafetyEnabledExpr,
    SourceExpr,
    StyleExpr,
    TaskExpr,
    ToneExpr,
    ToolCallExpr,
    ToolExpr,
)


_REGISTRY: Dict[str, Type[Expression]] = {
    "persona": PersonaExpr,
    "task": TaskExpr,
    "length": LengthExpr,
    "format": FormatExpr,
    "tone": ToneExpr,
    "source": SourceExpr,
    "style": StyleExpr,
    "behavior": BehaviorExpr,
    "safety_enabled": SafetyEnabledExpr,
    "format_markdown": FormatMarkdownExpr,
    "include_citations": IncludeCitationsExpr,
    "tool": ToolExpr,
    "args": ArgsExpr,
    "tool_call": ToolCallExpr,
}

# A live view keeps the public list synchronized with register_key().
KNOWN_KEYS: KeysView[str] = _REGISTRY.keys()


def register_key(key: str, expr_cls: Type[Expression]) -> None:
    """
    Register a new DSL key with its corresponding Expression class.
    Keys are stored lowercase. Raises ValueError if key already registered.
    """
    k = key.lower()
    if k in _REGISTRY:
        raise ValueError(f"DSL key '{k}' is already registered.")
    _REGISTRY[k] = expr_cls


def resolve_key(key: str) -> Optional[Type[Expression]]:
    """Return the expression class registered for ``key``, if any."""
    return _REGISTRY.get(key.lower())


def get_registered() -> Dict[str, Type[Expression]]:
    """Return a copy of the registered key → Expression class mapping."""
    return dict(_REGISTRY)
