from __future__ import annotations

"""
Observer contract and in-process EventBus for Mêtis.

Design choices:
- In-process: simple and appropriate for the current architecture
- Synchronous: deterministic and easy to test
- Minimal API: enough for typed and global subscriptions

This implementation supports:
- subscribing to a specific event type
- subscribing to all events
- unsubscribing from both
- publishing an event to matching observers
"""

from collections import defaultdict
from threading import RLock
from typing import DefaultDict, Protocol, runtime_checkable

from .event import Event


@runtime_checkable
class Observer(Protocol):
    """
    Observer contract used by the EventBus.

    Any observer must implement notify(event), allowing concrete observers
    such as LoggingObserver, MetricsObserver, and SafetyObserver to react
    to published events.
    """

    def notify(self, event: Event) -> None:
        """
        Handle a published event.

        Args:
            event:
                The structured event emitted by a publisher.
        """
        ...


class EventBus:
    """
    In-process event dispatcher for the Observer Pattern.

    The EventBus routes events from publishers to interested observers.

    Subscription modes:
    - specific event type: observer receives only matching events
    - global: observer receives all events

    Example:
        bus = EventBus()
        bus.subscribe("command.completed", metrics_observer)
        bus.subscribe_all(logging_observer)
        bus.publish(event)

    Thread-safety:
    - Uses a re-entrant lock to protect subscription mutation and snapshotting
    - Dispatch itself is synchronous and performed outside the lock where possible
      to avoid holding the lock while observer code runs
    """

    def __init__(self) -> None:
        # Maps event types (e.g. "command.completed") to observers.
        self._subscribers: DefaultDict[str, list[Observer]] = defaultdict(list)

        # Observers that receive every event.
        self._global_subscribers: list[Observer] = []

        # Protects subscription changes and snapshot reads.
        self._lock = RLock()

    def subscribe(self, event_type: str, observer: Observer) -> None:
        """
        Subscribe an observer to a specific event type.

        Duplicate registrations for the same observer and event type are ignored.

        Args:
            event_type:
                The event type to observe, e.g. "model.failed".

            observer:
                The observer instance to notify.
        """
        with self._lock:
            observers = self._subscribers[event_type]
            if observer not in observers:
                observers.append(observer)

    def subscribe_all(self, observer: Observer) -> None:
        """
        Subscribe an observer to all events.

        Duplicate global registrations are ignored.

        Args:
            observer:
                The observer instance to notify for every event.
        """
        with self._lock:
            if observer not in self._global_subscribers:
                self._global_subscribers.append(observer)

    def unsubscribe(self, event_type: str, observer: Observer) -> None:
        """
        Remove an observer from a specific event type subscription.

        If the observer is not currently subscribed, this is a no-op.

        Args:
            event_type:
                The event type previously subscribed to.

            observer:
                The observer instance to remove.
        """
        with self._lock:
            observers = self._subscribers.get(event_type)
            if not observers:
                return

            if observer in observers:
                observers.remove(observer)

            # Remove empty lists to keep the registry tidy.
            if not observers:
                self._subscribers.pop(event_type, None)

    def unsubscribe_all(self, observer: Observer) -> None:
        """
        Remove an observer from global subscriptions.

        If the observer is not globally subscribed, this is a no-op.

        Args:
            observer:
                The observer instance to remove.
        """
        with self._lock:
            if observer in self._global_subscribers:
                self._global_subscribers.remove(observer)

    def publish(self, event: Event) -> None:
        """
        Publish an event to all matching observers.

        Dispatch order:
        1. global subscribers
        2. type-specific subscribers

        We snapshot subscriber lists under the lock, then notify outside the
        lock so that observer code cannot block subscription changes.

        Args:
            event:
                The structured event to dispatch.
        """
        with self._lock:
            global_subscribers = list(self._global_subscribers)
            typed_subscribers = list(self._subscribers.get(event.event_type, []))

        for observer in global_subscribers:
            observer.notify(event)

        for observer in typed_subscribers:
            observer.notify(event)

    def has_subscribers(self, event_type: str) -> bool:
        """
        Return True if the given event type has direct subscribers.

        This method does not consider global subscribers; it answers only
        whether the event type itself has registered observers.

        Args:
            event_type:
                The event type to check.

        Returns:
            bool indicating whether typed subscribers exist.
        """
        with self._lock:
            return bool(self._subscribers.get(event_type))

    def clear(self) -> None:
        """
        Remove all subscriptions.

        Useful in tests where a fresh EventBus state is needed.
        """
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()