"""
Event infrastructure for Mêtis.

This package provides the core building blocks for implementing the
Observer Pattern in the system:

- Event: the structured event envelope used across the application
- Observer: the observer contract
- EventBus: the in-process event dispatcher

Keeping these exports in __init__.py makes imports elsewhere in the
codebase simpler and more readable, for example:

    from metis.events import Event, EventBus, Observer
"""

from .bus import EventBus, Observer
from .event import Event

__all__ = ["Event", "Observer", "EventBus"]