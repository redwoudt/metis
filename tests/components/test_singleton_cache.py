"""
Unit tests for the Singleton cache utility used to avoid redundant model instantiation.
"""

import pytest
from metis.models.singleton_cache import get_or_set

# A simple factory to test side effects
class FactoryCounter:
    def __init__(self):
        self.count = 0

    def make(self):
        self.count += 1
        return f"instance-{self.count}"

# Test that the first call creates a new instance
def test_singleton_cache_creates_once():
    counter = FactoryCounter()
    key = ("test", "model", 1)

    instance = get_or_set(key, counter.make)
    assert instance == "instance-1"
    assert counter.count == 1

# Test that repeated calls with same key do not recreate the instance
def test_singleton_cache_reuses_instance():
    from metis.models import singleton_cache
    singleton_cache._instance_cache.clear()  # Reset before test

    counter = FactoryCounter()
    key = ("test", "model", 1)

    instance1 = get_or_set(key, counter.make)
    instance2 = get_or_set(key, counter.make)
    instance3 = get_or_set(key, counter.make)

    assert instance1 == instance2 == instance3
    assert counter.count == 1  # Only created once
