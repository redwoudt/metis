"""
SessionManager is responsible for managing user sessions.
Sessions provide continuity across user interactions, enabling context-aware prompting.

How it works:
- Loads or initializes a session using a user ID.
- Maintains a history of prompts and responses.
- Supports appending to and retrieving the session history.

Expansion Ideas:
- Persist sessions to disk or cloud storage (e.g., Redis, S3, Firestore).
- Implement session expiration and archival.
- Add encryption for sensitive session data.
- Introduce versioning for session schema changes.
"""
import os
import pickle
from metis.components.session import Session

class SessionManager:
    def __init__(self, file_path="sessions.pkl"):
        """
        Initialize the SessionManager and load any saved sessions from disk.
        """
        self.file_path = file_path
        self.memory = self._load_sessions()

    def _load_sessions(self):
        """
        Load session data from the pickle file if it exists, else return an empty dict.
        """
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f:
                return pickle.load(f)
        return {}

    def _save_sessions(self):
        """
        Save the current in-memory sessions to disk using pickle.
        """
        with open(self.file_path, "wb") as f:
            pickle.dump(self.memory, f)

    def load_or_create(self, user_id):
        """
        Load an existing session for the given user_id, or create a new one if not found.
        The session includes the user's conversation engine, history, and preferences.
        """
        if user_id not in self.memory:
            self.memory[user_id] = Session(user_id=user_id)
        return self.memory[user_id]

    def save(self, user_id, session, prompt=None, response=None):
        """
        Save the session to memory and persist it to disk.
        Optionally, log the prompt and response to session history.
        """
        if prompt and response:
            session.history.append((prompt, response))
        self.memory[user_id] = session
        self._save_sessions()