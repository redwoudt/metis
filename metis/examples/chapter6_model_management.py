"""Demonstrate Factory selection, keyed reuse, and Proxy governance offline."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from metis.models.adapters.mock_adapter import MockAdapter
from metis.models.model_factory import ModelFactory
from metis.models.singleton_cache import clear_cache


BASE_CONFIG: dict[str, Any] = {
    "vendor": "mock",
    "model": "chapter-6",
    "policies": {"cache": True, "block_empty": True},
}


def run_demo() -> dict[str, Any]:
    """Return observable results from the Chapter 6 model-management path."""
    clear_cache()
    factory = ModelFactory({"mock": lambda model, **_: MockAdapter(model)})

    first = factory.resolve("analysis", BASE_CONFIG)
    first_response = first.respond("Explain keyed model reuse.")

    equivalent_config = {
        **BASE_CONFIG,
        "policies": dict(BASE_CONFIG["policies"]),
    }
    second = factory.resolve("analysis", equivalent_config)
    second_response = second.respond("Explain keyed model reuse.")

    changed_config = {
        **BASE_CONFIG,
        "policies": {**BASE_CONFIG["policies"], "cache": False},
    }
    changed = factory.resolve("analysis", changed_config)

    try:
        factory.resolve(
            "analysis",
            {"vendor": "missing", "model": "chapter-6", "policies": {}},
        )
    except ValueError as exc:
        unsupported_vendor_error = str(exc)
    else:  # pragma: no cover - the Factory contract requires a failure
        unsupported_vendor_error = ""

    return {
        "same_config_reused": first is second,
        "changed_policy_creates_new_proxy": changed is not first,
        "first_response": first_response,
        "second_response": second_response,
        "unsupported_vendor_error": unsupported_vendor_error,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic example and print its observable contracts."""
    del argv
    result = run_demo()
    print(f"SAME_CONFIG_REUSED={result['same_config_reused']}")
    print(
        "CHANGED_POLICY_CREATES_NEW_PROXY="
        f"{result['changed_policy_creates_new_proxy']}"
    )
    print(f"FIRST_RESPONSE={result['first_response']}")
    print(f"SECOND_RESPONSE={result['second_response']}")
    print(f"UNSUPPORTED_VENDOR_ERROR={result['unsupported_vendor_error']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
