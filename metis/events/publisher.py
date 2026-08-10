"""Publishing contract and neutral implementation for optional events."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .event import Event


@runtime_checkable
class EventPublisher(Protocol):
    """Minimal event capability required by publishing clients."""

    def publish(self, event: Event) -> None:
        """Publish an event according to the implementation's semantics."""
        ...


class NullEventPublisher:
    """Accept events without dispatching, storing, or acknowledging them."""

    __slots__ = ()

    def publish(self, event: Event) -> None:
        """Discard an event and preserve the caller's control flow."""
        return None
