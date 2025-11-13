# metis/models/model_factory.py
"""
Model Factory for Metis
-----------------------

Resolves a ModelClient adapter (Adapter pattern) for a given role+config,
wraps it in a ModelProxy for policy enforcement, and is typically injected
into a ModelManager (Bridge implementor).

"""

import logging
from typing import Any, Dict, Tuple, Optional, Callable

from metis.config import Config
from .singleton_cache import get_or_set
from .model_proxy import ModelProxy
from .adapters.base import ModelClient  # keep this import to satisfy isinstance checks in tests
from .adapters.openai_adapter import OpenAIAdapter
from .adapters.anthropic_adapter import AnthropicAdapter
from .adapters.mock_adapter import MockAdapter  # top-level import for pickle safety

logger = logging.getLogger(__name__)


def _merge_policies(base: Optional[Dict[str, Any]], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Shallow-merge policy dicts with `override` winning."""
    base = base or {}
    override = override or {}
    return {**base, **override}


def _flex_call(factory: Callable, **kwargs):
    """
    Call `factory` with a flexible signature to support various test doubles:
      1) factory(**kwargs)
      2) factory(vendor, model, policies)
      3) factory(model)
      4) factory()
    Returns the factory product or raises if factory itself errors in all modes.
    """
    try:
        return factory(**kwargs)
    except TypeError:
        pass
    try:
        return factory(kwargs.get("vendor"), kwargs.get("model"), kwargs.get("policies"))
    except TypeError:
        pass
    try:
        return factory(kwargs.get("model"))
    except TypeError:
        pass
    # last-chance no-arg call (may still raise if factory requires args)
    return factory()


class ModelFactory:
    @staticmethod
    def for_role(role: str, config: Dict[str, Any]) -> ModelClient:
        """
        Resolve and return a ModelClient (wrapped in ModelProxy) for the given role.

        Resolution precedence:
          1) Caller's `config` values (highest precedence)
          2) Role-specific defaults from Config.MODEL_REGISTRY[role] (fallbacks)

        Supports an optional `factory` in the registry entry to construct custom adapters.
        Always returns an object honoring the ModelClient interface (ModelProxy implements it).
        """
        # Caller's requested values
        caller_vendor = config.get("vendor")
        caller_model = config.get("model")
        caller_policies = config.get("policies", {})

        # Role-specific defaults (fallbacks only)
        registry: Dict[str, Any] = getattr(Config, "MODEL_REGISTRY", {}).get(role, {})  # type: ignore[attr-defined]

        # Final resolution with CALLER precedence
        vendor = caller_vendor if caller_vendor is not None else registry.get("vendor", "openai")
        model_name = caller_model if caller_model is not None else registry.get("model", "gpt-4o-mini")

        # Policies: registry provides defaults; caller overrides them
        policies = _merge_policies(registry.get("policies", {}), caller_policies)

        logger.debug(
            f"[ModelFactory] Resolving adapter for role='{role}', "
            f"vendor='{vendor}', model='{model_name}', policies={policies}"
        )

        # Strip keys consumed by the factory logic from kwargs passed to adapters/factories
        adapter_kwargs = {
            k: v
            for k, v in {**registry, **config}.items()
            if k not in ("vendor", "model", "policies", "factory")
        }

        # Optional custom factory (used by tests and advanced configs)
        registry_factory: Optional[Callable[..., Any]] = registry.get("factory")

        def create_proxy() -> ModelClient:
            # Prefer custom factory when provided
            if registry_factory:
                logger.debug(f"[ModelFactory] Using custom factory for role='{role}'")
                product = _flex_call(
                    registry_factory,
                    role=role,
                    vendor=vendor,
                    model=model_name,
                    policies=policies,
                    **adapter_kwargs,
                )

                # If already a ModelProxy, return as-is to avoid double wrapping
                if isinstance(product, ModelProxy):
                    return product

                # If it's a ModelClient adapter, wrap in ModelProxy
                if isinstance(product, ModelClient):
                    return ModelProxy(product, policies)

                # Duck-typed: accept anything with a callable .generate
                if hasattr(product, "generate") and callable(getattr(product, "generate")):
                    return ModelProxy(product, policies)

                logger.error(
                    f"[ModelFactory] Factory for role='{role}' must return something with generate(), got: {type(product)}"
                )
                raise TypeError(
                    "Custom factory must return a ModelClient, ModelProxy, or an object exposing .generate()."
                )

            # Built-in adapters by vendor
            if vendor == "openai":
                adapter = OpenAIAdapter(model=model_name, **adapter_kwargs)
            elif vendor == "anthropic":
                adapter = AnthropicAdapter(model=model_name, **adapter_kwargs)
            elif vendor == "mock":
                adapter = MockAdapter(model_name)
            else:
                logger.error(f"[ModelFactory] Unsupported vendor '{vendor}' for role '{role}'")
                raise ValueError(f"Unsupported vendor: {vendor}")

            return ModelProxy(adapter, policies)

        # Cache instances to ensure singleton behavior across identical (vendor, model, policies)
        policies_key: Tuple[Tuple[str, Any], ...] = tuple(sorted(policies.items()))
        cache_key = (vendor, model_name, policies_key)
        client = get_or_set(cache_key, create_proxy)

        logger.debug(
            f"[ModelFactory] Returning cached ModelClient proxy for role='{role}' "
            f"({vendor}:{model_name})"
        )
        return client