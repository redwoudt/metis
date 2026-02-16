# memory/manager.py

import os
import pickle
from metis.memory.snapshot import ConversationSnapshot


class MemoryManager:
    """
    Acts as the Caretaker in the Memento Pattern.
    Responsible for managing a history of snapshots without needing to understand their contents.
    """

    def __init__(self, file_path="snapshots.pkl"):
        self._file_path = file_path
        self._snapshots = self._load_from_disk()

    def _load_from_disk(self):
        """
        Load the snapshot stack from disk, if available.
        """
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "rb") as f:
                    snapshots = pickle.load(f)
                    return snapshots if isinstance(snapshots, list) else []
            except Exception:
                return []
        return []

    def _save_to_disk(self):
        """
        Persist the snapshot stack to disk.
        """
        with open(self._file_path, "wb") as f:
            pickle.dump(self._snapshots, f)

    def save(self, snapshot):
        """
        Save a new snapshot to the top of the stack and persist to disk.

        :param snapshot: A ConversationSnapshot instance created by the Originator.
        """
        if snapshot is None:
            return
        self._snapshots.append(snapshot)
        self._save_to_disk()

    def restore_last(self):
        """
        Restore the most recent snapshot from the stack.

        :return: The latest snapshot if available; otherwise an empty ConversationSnapshot.
        """
        if self._snapshots:
            snapshot = self._snapshots.pop()
            self._save_to_disk()
            return snapshot

        # IMPORTANT: Return an empty snapshot instead of None
        return ConversationSnapshot({})

    def clear(self):
        """
        Clear all saved snapshots.
        Useful when resetting the conversation or after critical errors.
        """
        self._snapshots.clear()
        self._save_to_disk()