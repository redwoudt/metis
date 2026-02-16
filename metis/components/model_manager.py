from __future__ import annotations
"""
ModelManager acts as the Bridge implementor, routing text generation requests to a unified model interface.

Contract (test-aligned and stable):
- generate(...) -> str
- respond(...)  -> str (thin alias)

Adapters and proxies may return richer payloads internally, but ModelManager
is the *single normalization point* that always returns plain text.
"""

from typing import Any

from metis.models.adapters.base import RespondingModel
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, model_client: RespondingModel):
        self.model_client: RespondingModel = model_client
        logger.debug("[ModelManager] model_client=%s", type(self.model_client).__name__)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from the active model.

        This method intentionally returns a plain string to preserve
        backwards compatibility with tests and existing call sites.
        """
        # Preferred path: adapters / proxies exposing `generate()`
        if hasattr(self.model_client, "generate") and callable(getattr(self.model_client, "generate")):
            out = getattr(self.model_client, "generate")(prompt, **kwargs)

            if isinstance(out, dict):
                return str(out.get("text", ""))
            if isinstance(out, str):
                return out
            return ""

        # Fallback: minimal responding interface
        return self.model_client.respond(prompt, **kwargs)

    def respond(self, prompt: str, **kwargs: Any) -> str:
        """Alias for generate(); exposed for conversational flow."""
        return self.generate(prompt, **kwargs)
