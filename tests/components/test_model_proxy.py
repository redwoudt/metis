"""
Unit tests for ModelProxy under the Adapter + Bridge architecture.

These tests ensure that:
- Logging occurs when the log policy is enabled.
- Caching prevents repeated backend calls.
- Empty prompts can be blocked via policy.
- Rate limiting raises an exception when exceeded.

A lightweight DummyClient is used as the wrapped ModelClient adapter.
"""

import time
import pytest
from typing import Any, Dict

from metis.models.model_proxy import ModelProxy
from metis.models.adapters.base import ModelClient


class DummyClient(ModelClient):
    """Minimal fake adapter that simulates a backend model call."""

    def __init__(self):
        self.provider = "dummy"
        self.model = "v1"
        self.call_log = []

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Simulate a model call with predictable output."""
        self.call_log.append(prompt)
        text = f"[dummy:{self.model}] {prompt.strip() or '<empty>'}"
        return {
            "text": text,
            "provider": self.provider,
            "model": self.model,
            "tokens_in": len(prompt.split()),
            "tokens_out": len(text.split()),
            "latency_ms": 0,
            "cost": 0.0,
        }


def test_proxy_logging_enabled(caplog):
    """Test that logging occurs when the log policy is enabled."""
    caplog.set_level("DEBUG", logger="metis.models.model_proxy")

    backend = DummyClient()
    proxy = ModelProxy(backend, policies={"log": True})
    output = proxy.generate("Hello!")

    assert isinstance(output, dict)
    assert any("[proxy]" in r.message for r in caplog.records)


def test_proxy_caching_enabled():
    """Test that caching returns the cached result on repeated calls."""
    backend = DummyClient()
    proxy = ModelProxy(backend, policies={"cache": True})

    result1 = proxy.generate("Repeat this")
    result2 = proxy.generate("Repeat this")

    assert result1 == result2
    assert len(backend.call_log) == 1  # Only one backend call executed


def test_proxy_blocks_empty_prompt():
    """Test that empty prompts are blocked when block_empty is set."""
    backend = DummyClient()
    proxy = ModelProxy(backend, policies={"block_empty": True})

    response = proxy.generate("   ")  # whitespace prompt
    assert response == "[blocked: empty prompt]"
    assert len(backend.call_log) == 0


def test_proxy_rate_limiting_throws():
    """Test that rate limiting raises an exception when exceeded."""
    backend = DummyClient()
    # A tiny delay window simulates a near-zero rate limit
    proxy = ModelProxy(backend, policies={"max_rps": 1000})

    proxy.generate("Prompt 1")
    with pytest.raises(Exception, match="Rate limit exceeded"):
        proxy.generate("Prompt 2")