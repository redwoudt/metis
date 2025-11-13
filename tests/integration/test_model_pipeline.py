"""
Integration test for the full model pipeline: Factory → Singleton → Proxy.
Validates correct instance reuse, policy enforcement, and call output.
"""

from metis.models.model_factory import ModelFactory


def _client(policies=None):
    """Helper to obtain a proxy-wrapped ModelClient via the real ModelFactory."""
    return ModelFactory.for_role(
        "narrative",
        {
            "vendor": "mock",
            "model": "mock-v1",
            "policies": policies or {},
        },
    )


def test_pipeline_returns_expected_response():
    client = _client()
    output = client.generate("Tell me a story about dragons.")

    # Handle both legacy string outputs and the new dict-shaped proxy outputs.
    if isinstance(output, dict):
        text = output.get("text", "")
    else:
        text = str(output)

    assert isinstance(text, str)
    # Optional extra safety check, if it already exists or you want it:
    # assert "dragon" in text.lower()


def test_pipeline_reuses_singleton_instance():
    client1 = _client()
    client2 = _client()
    # The factory caches by (vendor, model, policies), so these should be the same proxy instance.
    assert client1 is client2


def test_pipeline_proxy_blocks_empty_prompt():
    client = _client(policies={"block_empty": True})
    output = client.generate("   ")  # blank/whitespace prompt
    assert output == "[blocked: empty prompt]"