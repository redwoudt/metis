"""
Tests for ToolExecutor functionality including tool dispatching and error handling.
"""

from metis.components.tool_executor import ToolExecutor
import pytest


def test_tool_executor_weather():
    executor = ToolExecutor()
    output = executor.execute("weather", "Weather update")
    assert isinstance(output, str)
    assert len(output) > 0


def test_tool_executor_unknown():
    executor = ToolExecutor()
    with pytest.raises(Exception):
        executor.execute("unknown_tool", "test input")
