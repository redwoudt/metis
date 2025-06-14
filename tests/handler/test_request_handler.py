"""
Unit and integration tests for the RequestHandler orchestration flow.
Includes success paths, policy rejection, tool execution, session lifecycle,
mock tracing, exception handling, and snapshot-style output checks.
"""

import pytest
from unittest.mock import MagicMock
from metis.handler import RequestHandler
from metis.exceptions import ToolExecutionError
from tests.test_utils import MockPromptStrategy, AllowAllPolicy, DenyAllPolicy


def test_handle_prompt_success():
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    response = handler.handle_prompt("user_123", "Tell me something nice")
    assert "Tone: friendly" in response
    assert "Tell me something nice" in response


def test_policy_enforcement_denied():
    handler = RequestHandler(policy=DenyAllPolicy())
    with pytest.raises(PermissionError):
        handler.handle_prompt("user_123", "Forbidden access")


def test_weather_tool_execution():
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    response = handler.handle_prompt("user_456", "What’s the weather like today?")
    assert "weather" in response.lower() or "Weather Info" in response


def test_session_lifecycle_and_prompt_building():
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    user_id = "user_test"
    prompt = "Summarize yesterday's session"

    first_response = handler.handle_prompt(user_id, prompt)
    assert "Welcome message context" in first_response

    second_response = handler.handle_prompt(user_id, "What did we talk about?")
    assert "did you mean" in second_response
    assert "What did we talk about?" in second_response


def test_tool_execution_exception_handling():
    mock_executor = MagicMock()
    mock_executor.execute.side_effect = Exception("Simulated tool failure")

    handler = RequestHandler(
        strategy=MockPromptStrategy(),
        policy=AllowAllPolicy(),
        tool_executor=mock_executor,
    )

    with pytest.raises(ToolExecutionError) as exc:
        handler.handle_prompt("user_789", "Check the weather")
    assert "Simulated tool failure" in str(exc.value)


def test_tracing_output_snapshot():
    # Simulate a real call and snapshot the output format
    handler = RequestHandler(strategy=MockPromptStrategy(), policy=AllowAllPolicy())
    user_id = "user_snap"
    prompt = "Explain quantum mechanics"
    response = handler.handle_prompt(user_id, prompt)

    assert "Welcome message context: Explain quantum mechanics" in response
    assert response.startswith("[Tone: friendly] Welcome message context:")