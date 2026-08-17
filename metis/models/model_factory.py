"""Registry-backed model Factory with Adapter, Proxy, and Singleton support."""

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, cast

from metis.config import Config

from .adapters.anthropic_adapter import AnthropicAdapter
from .adapters.base import RespondingModel
from .adapters.mock_adapter import MockAdapter
from .adapters.openai_adapter import OpenAIAdapter
from .model_client import ModelClient
from .model_proxy import ModelProxy
from .singleton_cache import get_or_set

logger = logging.getLogger(__name__)

AdapterFactory = Callable[..., Any]


def _merge_policies(
    base: Optional[Dict[str, Any]],
    override: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Shallow-merge policy dictionaries with ``override`` winning."""
    return {**(base or {}), **(override or {})}


def _openai_factory(
    *,
    model: str,
    role: str | None = None,
    vendor: str | None = None,
    policies: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ModelClient:
    return OpenAIAdapter(model=model, **kwargs)


def _anthropic_factory(
    *,
    model: str,
    role: str | None = None,
    vendor: str | None = None,
    policies: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ModelClient:
    return AnthropicAdapter(model=model, **kwargs)


def _mock_factory(
    *,
    model: str,
    role: str | None = None,
    vendor: str | None = None,
    policies: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ModelClient:
    return MockAdapter(model)


def default_adapter_factories() -> dict[str, AdapterFactory]:
    """Return a fresh registry containing the three built-in providers."""
    return {
        "openai": _openai_factory,
        "anthropic": _anthropic_factory,
        "mock": _mock_factory,
    }


def _flex_call(factory: AdapterFactory, **kwargs: Any) -> Any:
    """Support the factory signatures already accepted by Mêtis tests/config."""
    try:
        return factory(**kwargs)
    except TypeError:
        pass
    try:
        return factory(
            kwargs.get("vendor"),
            kwargs.get("model"),
            kwargs.get("policies"),
        )
    except TypeError:
        pass
    try:
        return factory(kwargs.get("model"))
    except TypeError:
        pass
    return factory()


def _proxy_product(
    product: Any,
    *,
    policies: Dict[str, Any],
    source: str,
) -> ModelClient:
    if product is None:
        raise TypeError(f"{source} returned None; expected a model client")
    if isinstance(product, str):
        raise TypeError(f"{source} returned text; expected a model client")

    if isinstance(product, RespondingModel) and not (
        hasattr(product, "generate") and callable(getattr(product, "generate"))
    ):

        class _RespondOnlyAdapter(ModelClient):
            def __init__(self, inner: RespondingModel):
                self._inner = inner

            def generate(self, prompt: str, **kwargs: Any) -> str:
                return self._inner.respond(prompt, **kwargs)

        product = _RespondOnlyAdapter(product)

    if isinstance(product, ModelProxy):
        return product
    if isinstance(product, ModelClient):
        return ModelProxy(product, policies)
    if hasattr(product, "generate") and callable(getattr(product, "generate")):
        return ModelProxy(cast(ModelClient, product), policies)
    raise TypeError(
        f"{source} must return a ModelClient, ModelProxy, or object exposing generate()"
    )


class ModelFactory:
    """Resolve model clients from an injected vendor-to-factory registry."""

    def __init__(
        self,
        adapter_registry: Mapping[str, AdapterFactory] | None = None,
    ) -> None:
        self._adapter_registry = dict(
            adapter_registry
            if adapter_registry is not None
            else default_adapter_factories()
        )

    @property
    def adapter_registry(self) -> Mapping[str, AdapterFactory]:
        return MappingProxyType(self._adapter_registry)

    @classmethod
    def for_role(cls, role: str, config: Dict[str, Any]) -> ModelClient:
        """Compatibility entry point using only built-in adapter factories."""
        return cls().resolve(role, config)

    def resolve(self, role: str, config: Dict[str, Any]) -> ModelClient:
        """Resolve and proxy a model client for one configured role."""
        caller_vendor = config.get("vendor")
        caller_model = config.get("model")
        caller_policies = config.get("policies", {})

        role_config: Dict[str, Any] = getattr(Config, "MODEL_REGISTRY", {}).get(
            role,
            {},
        )
        vendor = (
            caller_vendor
            if caller_vendor is not None
            else role_config.get("vendor", "openai")
        )
        model_name = (
            caller_model
            if caller_model is not None
            else role_config.get("model", "gpt-4o-mini")
        )
        policies = _merge_policies(role_config.get("policies", {}), caller_policies)
        adapter_kwargs = {
            key: value
            for key, value in {**role_config, **config}.items()
            if key not in ("vendor", "model", "policies", "factory")
        }

        registry_factory: Optional[AdapterFactory] = role_config.get("factory")
        factory = registry_factory or self._adapter_registry.get(str(vendor))
        if factory is None:
            logger.error(
                "[ModelFactory] Unsupported vendor '%s' for role '%s'",
                vendor,
                role,
            )
            raise ValueError(f"Unsupported vendor: {vendor}")

        def create_proxy() -> ModelClient:
            product = _flex_call(
                factory,
                role=role,
                vendor=vendor,
                model=model_name,
                policies=policies,
                **adapter_kwargs,
            )
            return _proxy_product(
                product,
                policies=policies,
                source=f"Adapter factory for vendor '{vendor}'",
            )

        policies_key: Tuple[Tuple[str, Any], ...] = tuple(sorted(policies.items()))
        # Preserve the existing cache contract so callers upgrading to the
        # registry-backed factory see identical singleton behaviour.
        cache_key = (str(vendor), model_name, policies_key)
        client = cast(ModelClient, get_or_set(cache_key, create_proxy))
        logger.debug(
            "[ModelFactory] Returning cached client for role='%s' (%s:%s)",
            role,
            vendor,
            model_name,
        )
        return client
