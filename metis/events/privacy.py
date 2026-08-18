"""Privacy-safe summaries for exported lifecycle events.

Events are often forwarded to logs, analytics, and third-party telemetry.  The
helpers in this module keep raw prompts, arguments, results, and exception
messages out of the default event surface while retaining enough structure for
correlation, alerting, and capacity planning.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping


def content_summary(value: Any) -> dict[str, Any]:
    """Describe content without exporting the content itself."""
    text = "" if value is None else str(value)
    return {
        "content_length": len(text),
        "content_sha256": sha256(text.encode("utf-8")).hexdigest(),
    }


def argument_summary(arguments: Mapping[str, Any] | None) -> dict[str, Any]:
    """Describe a command argument shape without exporting argument values."""
    names = sorted(str(name) for name in (arguments or {}))
    return {
        "argument_count": len(names),
        "argument_names": names,
    }


def result_summary(result: Any) -> dict[str, Any]:
    """Describe a result's shape without copying its potentially sensitive value."""
    summary: dict[str, Any] = {"result_type": type(result).__name__}
    if isinstance(result, Mapping):
        summary["result_keys"] = sorted(str(name) for name in result)
    elif isinstance(result, (str, bytes, list, tuple, set)):
        summary["result_length"] = len(result)
    return summary


def exception_summary(exc: BaseException) -> dict[str, str]:
    """Return the stable failure category without the exception message."""
    return {"error_type": exc.__class__.__name__}
