# tests/memory/test_snapshot.py

from metis.memory.snapshot import ConversationSnapshot


def test_snapshot_stores_deepcopy():
    """
    Creating a ConversationSnapshot should deep-copy the provided state so that
    subsequent mutations to the original do not affect the stored snapshot.
    """
    state = {"nested": {"a": 1}, "list": [1, 2, 3]}
    snapshot = ConversationSnapshot(state)

    # Mutate original after snapshot creation
    state["nested"]["a"] = 999
    state["list"].append(4)

    restored = snapshot.get_state()
    assert restored["nested"]["a"] == 1
    assert restored["list"] == [1, 2, 3]


def test_restored_state_is_independent_of_snapshot():
    """
    Modifying the state returned from get_state() should not mutate the
    snapshot's internal storage (i.e., get_state returns a deep copy each time).
    """
    snapshot = ConversationSnapshot({"cfg": {"x": 10}, "arr": [1]})

    # First restore and mutate the restored copy
    restored1 = snapshot.get_state()
    restored1["cfg"]["x"] = 42
    restored1["arr"].append(2)

    # A fresh restore should NOT reflect mutations made to restored1
    restored2 = snapshot.get_state()
    assert restored2["cfg"]["x"] == 10
    assert restored2["arr"] == [1]