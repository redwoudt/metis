import pytest
from metis.handler import RequestHandler
from tests.test_utils import MockPromptStrategy, AllowAllPolicy, DenyAllPolicy


def test_handle_prompt_success():
    handler = RequestHandler(
        strategy=MockPromptStrategy(),
        policy=AllowAllPolicy()
    )
    response = handler.handle_prompt("user_123", "Tell me something nice")
    assert "MockPrompt" in response


def test_policy_enforcement_denied():
    handler = RequestHandler(policy=DenyAllPolicy())
    with pytest.raises(PermissionError):
        handler.handle_prompt("user_123", "Forbidden access")

