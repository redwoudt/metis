

"""
Unit tests for the ModelProxy class that wraps model calls with policy-based behaviors.
"""

import time
import pytest
from metis.models.model_proxy import ModelProxy
from tests.test_utils import MockModel

# Test that logging occurs when the log policy is enabled
def test_proxy_logging_enabled(capsys):
    backend = MockModel()
    proxy = ModelProxy(backend, policies={"log": True})
    output = proxy.generate("Hello!")

    captured = capsys.readouterr()
    assert "[proxy]" in captured.out
    assert output.startswith("Mocked:")

# Test that caching returns the cached result on repeated calls
def test_proxy_caching_enabled():
    backend = MockModel()
    proxy = ModelProxy(backend, policies={"cache": True})

    result1 = proxy.generate("Repeat this")
    result2 = proxy.generate("Repeat this")

    assert result1 == result2
    assert len(backend.call_log) == 1  # Only one backend call

# Test that empty prompts are blocked when block_empty is set
def test_proxy_blocks_empty_prompt():
    backend = MockModel()
    proxy = ModelProxy(backend, policies={"block_empty": True})

    response = proxy.generate("   ")  # whitespace prompt
    assert response == "[blocked: empty prompt]"
    assert len(backend.call_log) == 0

# Test that rate limiting raises an exception when exceeded
def test_proxy_rate_limiting_throws():
    backend = MockModel()
    proxy = ModelProxy(backend, policies={"max_rps": 1000})  # very low delay allowed

    proxy.generate("Prompt 1")
    with pytest.raises(Exception, match="Rate limit exceeded"):
        proxy.generate("Prompt 2")