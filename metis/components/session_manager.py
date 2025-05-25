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

class SessionManager:
    def __init__(self):
        self.memory = {}

    def load_or_create(self, user_id):
        if user_id not in self.memory:
            self.memory[user_id] = {"user_id": user_id, "history": []}
        return self.memory[user_id]

    def save(self, user_id, session, prompt, response):
        if user_id not in self.memory:
            self.memory[user_id] = session
        self.memory[user_id]["history"].append((prompt, response))
