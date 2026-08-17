"""Entry-point discovery without importing advertised plugin code."""

from __future__ import annotations

from importlib import metadata
from typing import Any, Callable, Iterable


PLUGIN_ENTRY_POINT_GROUP = "metis_genai.plugins"


def discover_plugins(
    *,
    group: str = PLUGIN_ENTRY_POINT_GROUP,
    entry_points_provider: Callable[[], Any] = metadata.entry_points,
) -> tuple[Any, ...]:
    """Return deterministic entry-point metadata for the owned plugin group."""
    discovered = entry_points_provider()
    if hasattr(discovered, "select"):
        candidates: Iterable[Any] = discovered.select(group=group)
    elif isinstance(discovered, dict):  # Python/backport compatibility
        candidates = discovered.get(group, ())
    else:
        candidates = (ep for ep in discovered if getattr(ep, "group", None) == group)

    return tuple(sorted(candidates, key=_sort_key))


def _sort_key(entry_point: Any) -> tuple[str, str, str]:
    distribution = getattr(entry_point, "dist", None)
    distribution_name = str(getattr(distribution, "name", ""))
    value = str(getattr(entry_point, "value", ""))
    return (str(entry_point.name), distribution_name, value)
