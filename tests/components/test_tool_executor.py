from metis.components.tool_executor import ToolExecutor


def test_tool_executor_weather():
    executor = ToolExecutor()
    result = executor.execute("weather", "What’s the weather today?")
    assert isinstance(result, str) and len(result) > 0
