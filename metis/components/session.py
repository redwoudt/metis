# metis/components/session.py
from metis.conversation_engine import ConversationEngine
from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager
import os

class Session:
    def __init__(self, user_id=None, engine=None, history=None, preferences=None):
        self.user_id = user_id
        if engine is None:
            vendor = os.getenv("METIS_VENDOR", "mock")
            model = os.getenv("METIS_MODEL", "stub")
            client = ModelFactory.for_role("analysis", {"vendor": vendor, "model": model, "policies": {}})
            engine = ConversationEngine(model_manager=ModelManager(client))
        self.engine = engine
        self.history = history or []
        self.preferences = preferences or {}
        # keep rest unchanged