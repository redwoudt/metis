"""
Model Factory for Metis
------------------------
Centralizes creation and configuration of models based on logical roles.
Integrates with Singleton cache for reuse and wraps models with a Proxy
to enforce operational policies.
"""

import logging
logger = logging.getLogger(__name__)

from typing import Any, Callable, Dict
from .singleton_cache import get_or_set
from .model_proxy import ModelProxy

class ModelFactory:
    # Initialize the factory with a registry mapping roles to model configurations
    def __init__(self, registry: Dict[str, Dict[str, Any]]):
        self.registry = registry

    # Retrieve a model for a given role using the config registry.
    # Applies singleton caching to prevent duplicate model instantiations.
    # Wraps the result with a Proxy for enforcing operational policies.
    def get_model(self, role: str) -> Any:
        logger.debug(f"[ModelFactory] Getting model for role: {role}")
        config = self.registry.get(role)
        if config is None:
            raise ValueError(f"No model configuration found for role: {role}")

        # Vendor-specific instantiation logic wrapped with ModelProxy caching
        def create_proxy():
            vendor = config.get("vendor")
            logger.warning(f"[ModelFactory] Vendor '{vendor}' requested for role '{role}' with config: {config}")

            if vendor == "openai":
                from openai_model import OpenAIModel
                model_instance = OpenAIModel(config)
            elif vendor == "huggingface":
                from huggingface_model import HuggingFaceModel
                model_instance = HuggingFaceModel(config)
            elif vendor == "mock":
                from tests.test_utils import MockModel
                model_instance = MockModel(config)
            else:
                logger.error(f"[ModelFactory] Unsupported vendor: {vendor}")
                raise ValueError(f"Unsupported vendor: {vendor}")

            return ModelProxy(model_instance, config.get("policies", {}))

        key = tuple(sorted(config.items()))
        model_proxy = get_or_set(key, create_proxy)
        logger.debug(f"[ModelFactory] Returning cached ModelProxy for role: {role}")
        return model_proxy