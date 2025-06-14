# tests/memory/test_snapshot.py

from metis.memory.snapshot import ConversationSnapshot

def test_snapshot_stores_deepcopy():
    state = {"nested": {"a": 1}}
    snapshot = ConversationSnapshot(state)

    state["nested"]["a"] = 999  # Mutate original

    restored = snapshot.get_state()
    assert restored["nested"]["a"] == 1