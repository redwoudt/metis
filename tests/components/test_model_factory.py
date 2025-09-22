"""
Unit tests for ModelFactory demonstrating integration with Singleton and Proxy patterns.
"""

import pytest
from metis.models.model_factory import ModelFactory
from tests.test_utils import MockModel

# A mock registry that defines a single role and its model configuration
@pytest.fixture
def registry():
    return {
        "test-role": {
            "vendor": "mock",
            "model": "mock-model",
            "defaults": {
                "temperature": 0.5
            },
            "policies": {
                "log": True,
                "cache": False
            }
        }
    }

# A factory fixture that uses the mock registry and injects a mock model creator
@pytest.fixture
def factory(monkeypatch, registry):
    def fake_create_model(*args, **kwargs):
        return MockModel(**kwargs)

    monkeypatch.setitem(registry, "test-role", {
        **registry["test-role"],
        "factory": fake_create_model
    })

    # Subclass ModelFactory to override get_model for testing with mocks
    class TestModelFactory(ModelFactory):
        def get_model(self, role: str):
            cfg = self.registry[role]
            key = (cfg["vendor"], cfg["model"], frozenset(cfg.get("defaults", {}).items()))

            def create():
                return cfg["factory"](**cfg.get("defaults", {}))

            from metis.models.singleton_cache import get_or_set
            instance = get_or_set(key, create)

            from metis.models.model_proxy import ModelProxy
            return ModelProxy(instance, cfg.get("policies", {}))

    return TestModelFactory(registry)

# Test that the factory returns a Proxy-wrapped model that logs calls
def test_factory_returns_proxy_wrapped_model(factory):
    model = factory.get_model("test-role")
    output = model.generate("Hello world")

    assert isinstance(model.backend, MockModel)
    assert output.startswith("Mocked:")
    assert model.backend.call_log[0] == "Hello world"

# Test that calling get_model twice returns the same instance (Singleton)
def test_factory_singleton_reuse(factory):
    model1 = factory.get_model("test-role")
    model2 = factory.get_model("test-role")

    assert model1.backend is model2.backend
