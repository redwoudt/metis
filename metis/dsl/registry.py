

"""
Lightweight registry to extend the DSL with new keys → expression classes.
"""
from typing import Dict, Type
from .ast import Expression

_REGISTRY: Dict[str, Type[Expression]] = {}

def register_key(key: str, expr_cls: Type[Expression]) -> None:
    """
    Register a new DSL key with its corresponding Expression class.
    Keys are stored lowercase. Raises ValueError if key already registered.
    """
    k = key.lower()
    if k in _REGISTRY:
        raise ValueError(f"DSL key '{k}' is already registered.")
    _REGISTRY[k] = expr_cls

def get_registered() -> Dict[str, Type[Expression]]:
    """Return a copy of the registered key → Expression class mapping."""
    return dict(_REGISTRY)