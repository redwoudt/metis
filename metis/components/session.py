# metis/components/session.py

from metis.conversation_engine import ConversationEngine

class Session:
    def __init__(self, user_id=None, engine=None, history=None, preferences=None):
        self.user_id = user_id
        self.engine = engine or ConversationEngine()
        self.history = history or []
        self.preferences = preferences or {}