"""
Tests for ModelFactory.for_role(...) returning proxy-wrapped ModelClient adapters.

Covers:
- Returns a ModelProxy that still honors the ModelClient interface
- Caches instances by (vendor, model, policies)
- Produces usable .generate(...) output
- Handles unsupported vendors with a clear error
"""

import pytest

from metis.models.model_factory import ModelFactory
from metis.models.model_proxy import ModelProxy
from metis.models.adapters.base import ModelClient


def test_factory_returns_proxy_wrapped_adapter_openai():
    cfg = {"vendor": "openai", "model": "gpt-4o-mini", "policies": {"limit": "soft"}}
    client = ModelFactory.for_role("analysis", cfg)
    assert isinstance(client, ModelProxy), "Factory should wrap adapters in ModelProxy"
    assert isinstance(client, ModelClient), "Proxy must honor ModelClient interface"


def test_factory_returns_proxy_wrapped_adapter_anthropic():
    cfg = {"vendor": "anthropic", "model": "claude-3-sonnet", "policies": {}}
    client = ModelFactory.for_role("summary", cfg)
    assert isinstance(client, ModelProxy)
    assert isinstance(client, ModelClient)


def test_factory_mock_adapter_generates_text():
    cfg = {"vendor": "mock", "model": "stub", "policies": {}}
    client = ModelFactory.for_role("analysis", cfg)
    out = client.generate("Hello")
    assert isinstance(out, dict)
    assert isinstance(out["text"], str)
    assert "[mock:stub]" in out["text"].lower()


def test_factory_caching_same_key_returns_same_instance():
    cfg = {"vendor": "mock", "model": "stub", "policies": {"budget": 10}}
    a = ModelFactory.for_role("analysis", cfg)
    b = ModelFactory.for_role("analysis", cfg)
    assert a is b, "Same (vendor, model, policies) should return the cached instance"


def test_factory_caching_different_policies_returns_different_instance():
    cfg1 = {"vendor": "mock", "model": "stub", "policies": {"budget": 10}}
    cfg2 = {"vendor": "mock", "model": "stub", "policies": {"budget": 20}}
    a = ModelFactory.for_role("analysis", cfg1)
    b = ModelFactory.for_role("analysis", cfg2)
    assert a is not b, "Different policies should produce different cached instances"


def test_factory_unsupported_vendor_raises():
    cfg = {"vendor": "unknown_vendor", "model": "x", "policies": {}}
    with pytest.raises(ValueError):
        ModelFactory.for_role("analysis", cfg)