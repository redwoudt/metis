

"""
Integration test for the full model pipeline: Factory → Singleton → Proxy.
Validates correct instance reuse, policy enforcement, and call output.
"""

from metis.models.model_factory import ModelFactory
from metis.models.singleton_cache import get_or_set
from metis.models.model_proxy import ModelProxy
from tests.test_utils import MockModel

# A fake model creator for testing integration
def create_mock_model(**kwargs):
    return MockModel(**kwargs)

# Registry configured with mock vendor and proxy policies
REGISTRY = {
    "narrative": {
        "vendor": "mock",
        "model": "mock-v1",
        "defaults": {
            "temperature": 0.8,
            "max_tokens": 500
        },
        "policies": {
            "log": True,
            "cache": True,
            "block_empty": True
        },
        "factory": create_mock_model
    }
}

# Subclass the factory to override actual vendor instantiation
class TestModelFactory(ModelFactory):
    def get_model(self, role: str):
        cfg = self.registry[role]
        key = (cfg["vendor"], cfg["model"], frozenset(cfg.get("defaults", {}).items()))

        def create():
            return cfg["factory"](**cfg.get("defaults", {}))

        instance = get_or_set(key, create)
        return ModelProxy(instance, cfg.get("policies", {}))

def test_pipeline_returns_expected_response():
    factory = TestModelFactory(REGISTRY)
    model = factory.get_model("narrative")

    output = model.generate("Tell me a story about dragons.")
    assert output.startswith("Mocked:")
    assert "dragons" in output

def test_pipeline_reuses_singleton_instance():
    factory = TestModelFactory(REGISTRY)
    model1 = factory.get_model("narrative")
    model2 = factory.get_model("narrative")

    assert model1.backend is model2.backend

def test_pipeline_proxy_blocks_empty_prompt():
    factory = TestModelFactory(REGISTRY)
    model = factory.get_model("narrative")

    output = model.generate("   ")  # blank prompt
    assert output == "[blocked: empty prompt]"