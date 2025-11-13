"""
Tests for ModelManager (Bridge implementor) under the Adapter + Bridge design.

ModelManager should:
- Delegate generation to a unified ModelClient (adapter) returned by ModelFactory.
- Return plain text (not raw SDK dicts).
- Remain provider-agnostic (swapping adapters changes output without changing callers).
"""

from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager


def _make_manager(vendor: str, model: str) -> ModelManager:
    client = ModelFactory.for_role(
        role="analysis",
        config={"vendor": vendor, "model": model, "policies": {}},
    )
    return ModelManager(client)


def test_model_manager_generates_text_from_mock_adapter():
    manager = _make_manager("mock", "stub")
    out = manager.generate("Ping")
    assert isinstance(out, str)
    assert "[mock:stub]" in out.lower()


def test_model_manager_generates_text_openai_adapter():
    manager = _make_manager("openai", "gpt-4o-mini")
    out = manager.generate("Tell me a story")
    assert isinstance(out, str)
    # The mocked adapter prefixes output with provider/model info
    assert "openai" in out.lower()


def test_model_manager_generates_text_anthropic_adapter():
    manager = _make_manager("anthropic", "claude-3-sonnet")
    out = manager.generate("Summarize this")
    assert isinstance(out, str)
    assert "anthropic" in out.lower()


def test_swapping_adapters_changes_output():
    manager_a = _make_manager("mock", "A")
    out_a = manager_a.generate("hello world")
    assert "[mock:a]" in out_a.lower()

    # Swap to a different adapter by creating a new manager (provider-agnostic caller)
    manager_b = _make_manager("mock", "B")
    out_b = manager_b.generate("hello world")
    assert "[mock:b]" in out_b.lower()

    assert out_a != out_b, "Changing adapters should change the output prefix/text"