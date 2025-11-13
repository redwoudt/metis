# metis/models/adapters/mock_adapter.py
from typing import Any, Dict
from .base import ModelClient


class MockAdapter(ModelClient):
    """
    Deterministic mock model adapter used in tests.

    This adapter simulates a consistent provider response without any
    external API dependency. It’s used across integration and component
    tests to ensure that both Adapter and Bridge layers work correctly.

    """

    def __init__(self, model: str = "stub"):
        # Expose both names for compatibility with proxies/factories
        self.vendor = "mock"
        self.provider = "mock"
        self.model = (model or "stub").strip() or "stub"

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Simulate deterministic text generation for tests.

        Always returns a dict with at least:
        {
            "text": "...",
            "provider": "mock",
            "vendor": "mock",
            "model": "<model>",
            "tokens_in": int,
            "tokens_out": int,
            "latency_ms": 0,
            "cost": 0.0,
        }
        """
        prompt_str = "" if prompt is None else str(prompt)
        prefix = f"[mock:{self.model}]"
        text = f"{prefix} {prompt_str}".strip() or prefix

        # Simple token simulation
        tokens_in = int(kwargs.get("tokens_in", 0) or 0)
        tokens_out = len(text.split())

        return {
            "text": text,
            "provider": self.provider,
            "vendor": self.vendor,
            "model": self.model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": 0,
            "cost": 0.0,
        }

    def __repr__(self):
        """Readable debugging representation for logs/tests."""
        return f"<MockAdapter vendor={self.vendor} model={self.model}>"