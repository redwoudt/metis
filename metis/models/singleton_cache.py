"""
Singleton Cache Utility for Metis
---------------------------------
Provides a thread-safe mechanism to cache and reuse heavy or costly model instances
across the application lifecycle. This prevents redundant instantiations and improves
memory and compute efficiency.
"""

from threading import RLock
from typing import Any, Callable, Dict, Tuple

# Internal cache dictionary for storing model instances
_instance_cache: Dict[Tuple[Any, ...], Any] = {}
# Thread lock to ensure thread-safe access to the cache
_lock = RLock()

# Retrieves an existing instance from the cache or creates and stores it using the factory.
# Ensures thread-safe, single instantiation per configuration key.
def get_or_set(key: Tuple[Any, ...], factory: Callable[[], Any]) -> Any:
    with _lock:
        if key not in _instance_cache:
            _instance_cache[key] = factory()
        return _instance_cache[key]