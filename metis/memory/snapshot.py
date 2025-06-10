# memory/snapshot.py

import copy

class ConversationSnapshot:
    """
    Acts as the Memento in the Memento Pattern.
    Encapsulates a deep copy of the Originator's internal state at a point in time.
    """

    def __init__(self, state_data):
        """
        Create a snapshot of the provided state data.

        :param state_data: A dictionary representing the Originator's internal state (typically __dict__).
        """
        self._state_data = copy.deepcopy(state_data)  # Ensure no shared references

    def get_state(self):
        """
        Retrieve a deep copy of the saved state.
        Used by the Originator to restore its own state safely.

        :return: A deep copy of the saved internal state dictionary.
        """
        return copy.deepcopy(self._state_data)