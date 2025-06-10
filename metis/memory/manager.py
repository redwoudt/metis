# memory/manager.py

class MemoryManager:
    """
    Acts as the Caretaker in the Memento Pattern.
    Responsible for managing a history of snapshots without needing to understand their contents.
    """

    def __init__(self):
        self._snapshots = []  # Internal stack of saved snapshots

    def save(self, snapshot):
        """
        Save a new snapshot to the top of the stack.

        :param snapshot: A ConversationSnapshot instance created by the Originator.
        """
        self._snapshots.append(snapshot)

    def restore_last(self):
        """
        Restore the most recent snapshot from the stack.

        :return: The latest snapshot if available; otherwise None.
        """
        if self._snapshots:
            return self._snapshots.pop()
        return None

    def clear(self):
        """
        Clear all saved snapshots.
        Useful when resetting the conversation or after critical errors.
        """
        self._snapshots.clear()