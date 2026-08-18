"""Request-scoped outcome returned by the full workflow API."""

from __future__ import annotations

from dataclasses import dataclass

from metis.inspection.records import ExecutionTrace


@dataclass(frozen=True)
class RequestResult:
    """Immutable result for one request invocation.

    ``RequestHandler.handle_prompt`` continues to return a string for backwards
    compatibility.  New callers can use ``RequestHandler.run`` to receive the
    response together with its correlation identity and completed trace without
    reading mediator-level ``last_*`` state.
    """

    response: str
    correlation_id: str
    execution_trace: ExecutionTrace
    checkpoint_saved: bool = False
    checkpoint_restored: bool = False
