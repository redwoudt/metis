"""
Singleton Cache Utility for Metis
---------------------------------
Provides a thread-safe mechanism to cache and reuse heavy or costly model instances
across the application lifecycle. This prevents redundant instantiations and improves
memory and compute efficiency.

Functions:
    get_or_set(key, factory) -> Any
    clear_cache() -> None
"""

from threading import RLock
from typing import Any, Callable, Dict, Tuple

import logging

logger = logging.getLogger(__name__)

# Internal cache dictionary for storing model instances
_instance_cache: Dict[Any, Any] = {}
# Thread lock to ensure thread-safe access to the cache
_lock = RLock()

def make_hashable(value):
    if isinstance(value, dict):
        return tuple(sorted((make_hashable(k), make_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, set):
        return frozenset(make_hashable(v) for v in value)
    elif isinstance(value, tuple):
        return tuple(make_hashable(v) for v in value)
    elif callable(value):
        return getattr(value, "__name__", repr(value))
    else:
        return value

# Retrieves an existing instance from the cache or creates and stores it using the factory.
# Ensures thread-safe, single instantiation per configuration key.
def get_or_set(key: Tuple[Any, ...], factory: Callable[[], Any]) -> Any:
    hashable_key = make_hashable(key)
    with _lock:
        if hashable_key in _instance_cache:
            logger.debug(f"Cache hit for key: {hashable_key}")
        else:
            logger.debug(f"Cache miss for key: {hashable_key} — creating new instance")
        if hashable_key not in _instance_cache:
            _instance_cache[hashable_key] = factory()
        return _instance_cache[hashable_key]

# Clears the singleton cache. Useful for testing purposes.
def clear_cache():
    with _lock:
        logger.debug("Clearing singleton cache")
        _instance_cache.clear()