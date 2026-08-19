import pytest

from metis.examples.chapter8_governed_tools import WeatherCommand, build_executor
from metis.exceptions import ToolExecutionError


def test_weather_runs_through_the_strict_pipeline() -> None:
    executor = build_executor()

    result = executor.execute_tool(
        "weather",
        args={"city": "Ithaca"},
        user="reader-01",
    )

    assert result == {"city": "Ithaca", "forecast": "clear"}
    assert executor.services.quota.calls == [("reader-01", "weather")]


def test_weather_requires_a_city() -> None:
    executor = build_executor()

    with pytest.raises(ValueError, match="Missing city"):
        executor.execute_tool("weather", args={}, user="reader-01")


def test_unknown_tool_is_rejected() -> None:
    executor = build_executor()

    with pytest.raises(ToolExecutionError, match="Unknown tool"):
        executor.execute_tool("weather_forecast", args={}, user="reader-01")


def test_quota_denial_stops_weather_before_execution(monkeypatch) -> None:
    executor = build_executor(allow=False)

    def fail_if_called(self, context):
        pytest.fail("WeatherCommand.execute() must not run after quota denial")

    monkeypatch.setattr(WeatherCommand, "execute", fail_if_called)

    with pytest.raises(RuntimeError, match="Rate limit exceeded"):
        executor.execute_tool(
            "weather",
            args={"city": "Ithaca"},
            user="reader-01",
        )
