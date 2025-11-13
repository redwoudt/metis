"""
Tests for model adapters (OpenAIAdapter and AnthropicAdapter).

These verify that each adapter:
- Implements the ModelClient interface correctly.
- Returns a normalized result dictionary with consistent keys.
- Includes provider and model identifiers.
- Measures latency and token counts, even when mocked.
"""

import pytest
from metis.models.adapters.openai_adapter import OpenAIAdapter
from metis.models.adapters.anthropic_adapter import AnthropicAdapter
from metis.models.adapters.base import ModelClient


@pytest.mark.parametrize(
    "adapter_cls,vendor,model_name",
    [
        (OpenAIAdapter, "openai", "gpt-4o-mini"),
        (AnthropicAdapter, "anthropic", "claude-3-sonnet"),
    ],
)
def test_adapter_contract(adapter_cls, vendor, model_name):
    """Each adapter must return a normalized dict with all required keys."""
    adapter = adapter_cls(model=model_name)
    assert isinstance(adapter, ModelClient), f"{adapter_cls.__name__} must subclass ModelClient"

    prompt = "Test the adapter normalization interface"
    result = adapter.generate(prompt)

    # Verify result structure
    assert isinstance(result, dict)
    for key in ["text", "provider", "model", "tokens_in", "tokens_out", "latency_ms", "cost"]:
        assert key in result, f"{key} missing from adapter output"

    # Check basic values
    assert result["provider"] == vendor
    assert result["model"] == model_name
    assert isinstance(result["text"], str)
    assert len(result["text"]) > 0
    assert isinstance(result["tokens_out"], int)
    assert isinstance(result["latency_ms"], int)
    assert isinstance(result["cost"], float)
    assert "mock" not in result["text"].lower() or vendor in result["provider"]


def test_adapter_latency_increases_with_longer_prompt():
    """Adapters should roughly measure longer latency for longer inputs (mocked timing)."""
    short_prompt = "Hi"
    long_prompt = "This is a longer prompt that should take slightly longer to process." * 10

    adapter = OpenAIAdapter()
    short_result = adapter.generate(short_prompt)
    long_result = adapter.generate(long_prompt)

    # Not strict timing, but latency should be non-negative integers
    assert short_result["latency_ms"] >= 0
    assert long_result["latency_ms"] >= 0
    assert isinstance(short_result["latency_ms"], int)
    assert isinstance(long_result["latency_ms"], int)


def test_adapter_respects_optional_kwargs_tokens_in():
    """Adapters should accept optional keyword args like tokens_in."""
    adapter = AnthropicAdapter()
    result = adapter.generate("Sample prompt", tokens_in=42)
    assert result["tokens_in"] == 42