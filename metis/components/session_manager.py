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
import logging
from metis.components.session import Session

logger = logging.getLogger(__name__)

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
        Handles corrupted files gracefully during tests or CLI runs.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "rb") as f:
                    data = pickle.load(f)

                # Legacy format: {user_id: Session(...)}
                if isinstance(data, dict) and data:
                    sample_val = next(iter(data.values()))
                    if isinstance(sample_val, Session):
                        return data

                # New persisted format: {user_id: {"user_id": ..., "history": ...}}
                if isinstance(data, dict):
                    restored: dict[str, Session] = {}
                    for uid, payload in data.items():
                        if isinstance(payload, Session):
                            restored[uid] = payload
                            continue
                        if isinstance(payload, dict):
                            s = Session(user_id=payload.get("user_id", uid))
                            s.history = payload.get("history", [])
                            restored[uid] = s
                    return restored

                return {}
            except (EOFError, pickle.UnpicklingError):
                logger.warning(
                    "Session file %s is corrupted or empty. Starting with fresh memory.",
                    self.file_path,
                )
                return {}
        return {}

    def _sanitize_session_for_pickle(self, session):
        """
        NOTE: This should only be used on copies and must not mutate live in-memory sessions.
        Remove or nullify non-pickleable runtime objects from a session before pickling.
        """
        engine = getattr(session, "engine", None)
        if engine:
            if hasattr(engine, "model_manager"):
                engine.model_manager = None
            if hasattr(engine, "model"):
                engine.model = None
            if hasattr(engine, "request_handler"):
                delattr(engine, "request_handler")

    def _save_sessions(self):
        """Save the current sessions to disk.

        Important: Do NOT mutate in-memory sessions (they may hold runtime objects like engines).
        We persist only pickle-safe data and reconstruct Sessions on load.
        """
        persisted: dict[str, dict] = {}
        for uid, session in self.memory.items():
            # Persist only safe fields.
            persisted[uid] = {
                "user_id": getattr(session, "user_id", uid),
                "history": getattr(session, "history", []),
            }

        with open(self.file_path, "wb") as f:
            pickle.dump(persisted, f)

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