# tests/memory/test_memory_manager.py

"""
Unit tests for MemoryManager under the Adapter + Bridge architecture.

These tests ensure that:
- MemoryManager can save and restore ConversationSnapshot objects.
- Restoring a snapshot reinstates engine state, preferences, and model_manager.
- When no snapshots exist, restore_last() returns None.
"""

from metis.memory.manager import MemoryManager
from metis.memory.snapshot import ConversationSnapshot
from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager


def _engine():
    """Helper: create a ConversationEngine wired to a mock adapter."""
    client = ModelFactory.for_role(
        "analysis", {"vendor": "mock", "model": "stub", "policies": {}}
    )
    manager = ModelManager(client)
    return ConversationEngine(model_manager=manager)


def test_save_and_restore_snapshot_with_engine():
    """Verify saving and restoring a ConversationSnapshot with full engine context."""
    memory = MemoryManager()
    engine = _engine()

    # Mutate state before snapshot
    engine.preferences["tone"] = "serious"
    engine.history.append("Hello Metis!")

    snapshot = engine.create_snapshot()
    memory.save(snapshot)

    # Mutate engine after snapshot
    engine.preferences["tone"] = "playful"
    engine.history.append("This should be rolled back")

    # Restore from snapshot
    restored = memory.restore_last()
    assert isinstance(restored, ConversationSnapshot)

    engine.restore_snapshot(restored)

    # Validate restored attributes
    assert engine.preferences["tone"] == "serious"
    assert engine.history == ["Hello Metis!"]

    # Confirm model_manager still functions after restore
    response = engine.generate_with_model("Ping test")
    assert isinstance(response, str)
    assert "[mock:stub]" in response.lower()


def test_restore_empty_returns_none():
    """Restoring with no snapshots should return None (no crash)."""
    memory = MemoryManager()
    assert memory.restore_last() is None