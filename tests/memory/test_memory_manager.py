# tests/memory/test_memory_manager.py

from metis.memory.manager import MemoryManager
from metis.memory.snapshot import ConversationSnapshot

def test_save_and_restore_snapshot():
    manager = MemoryManager()
    snapshot = ConversationSnapshot({"test": 123})
    manager.save(snapshot)

    restored = manager.restore_last()
    assert isinstance(restored, ConversationSnapshot)
    assert restored.get_state()["test"] == 123

def test_restore_empty_returns_none():
    manager = MemoryManager()
    assert manager.restore_last() is None