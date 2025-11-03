import time
from typing import Any, Dict
from .base import ModelClient

class AnthropicAdapter(ModelClient):
    def __init__(self, model: str = "claude-3-sonnet", **config):
        self.provider = "anthropic"
        self.model = model
        self.config = config

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        start = time.time()

        # TODO: Replace this mock with a real client call
        # resp = anthropic_client.messages.create(model=self.model, messages=[{"role":"user","content":prompt}], **kwargs)
        # text = resp.content[0].text
        text = f"[Anthropic mock:{self.model}] {prompt[:200]}"

        latency_ms = int((time.time() - start) * 1000)
        return {
            "text": text,
            "provider": self.provider,
            "model": self.model,
            "tokens_in": kwargs.get("tokens_in", 0),
            "tokens_out": len(text.split()),
            "latency_ms": latency_ms,
            "cost": 0.0,
        }