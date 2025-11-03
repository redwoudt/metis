"""
Model Factory for Metis
-----------------------

Returns a ModelClient adapter (Adapter pattern) for a given role+config,
wrapped in a ModelProxy for policy enforcement. The adapter is then injected
into ModelManager (Bridge implementor).
"""

import logging
from typing import Any, Dict, Tuple

from .singleton_cache import get_or_set
from .model_proxy import ModelProxy
from .adapters.base import ModelClient
from .adapters.openai_adapter import OpenAIAdapter
from .adapters.anthropic_adapter import AnthropicAdapter

logger = logging.getLogger(__name__)


class ModelFactory:
    @staticmethod
    def for_role(role: str, config: Dict[str, Any]) -> ModelClient:
        vendor = config.get("vendor", "openai")
        model_name = config.get("model", "gpt-4o-mini")
        policies = config.get("policies", {})

        logger.debug(
            f"[ModelFactory] Resolving adapter for role='{role}', "
            f"vendor='{vendor}', model='{model_name}', policies={policies}"
        )

        def create_proxy() -> ModelClient:
            if vendor == "openai":
                adapter = OpenAIAdapter(model=model_name, **config)
            elif vendor == "anthropic":
                adapter = AnthropicAdapter(model=model_name, **config)
            elif vendor == "mock":
                class MockAdapter(ModelClient):
                    def __init__(self, model_id: str):
                        self.provider = "mock"
                        self.model = model_id
                    def generate(self, prompt: str, **kwargs):
                        mocked = f"[mock:{self.model}] {prompt}"
                        return {
                            "text": mocked,
                            "provider": self.provider,
                            "model": self.model,
                            "tokens_in": 0,
                            "tokens_out": len(mocked.split()),
                            "latency_ms": 0,
                            "cost": 0.0,
                        }
                adapter = MockAdapter(model_name)
            else:
                logger.error(f"[ModelFactory] Unsupported vendor '{vendor}' for role '{role}'")
                raise ValueError(f"Unsupported vendor: {vendor}")

            return ModelProxy(adapter, policies)

        # Cache instances by (vendor, model, policies) to avoid rebuilding proxies
        policies_key: Tuple[Tuple[str, Any], ...] = tuple(sorted(policies.items()))
        cache_key = (vendor, model_name, policies_key)
        client = get_or_set(cache_key, create_proxy)

        logger.debug(
            f"[ModelFactory] Returning cached ModelClient proxy for role='{role}' "
            f"({vendor}:{model_name})"
        )
        return client


# TODO:
# In a future iteration, we can reintroduce a registry mapping logical roles
# (e.g. "summarizer", "assistant", "moderator") to default configs. At that point,
# callers would pass only `role`, and ModelFactory would look up vendor/model/policies
# instead of requiring the full config each time.