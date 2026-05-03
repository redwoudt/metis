import logging
from types import SimpleNamespace

import pytest

from metis.exceptions import ToolExecutionError
from metis.tools import ToolExecutor


class DummyQuota:
    def __init__(self):
        self.calls = []

    def allow(self, user_id, tool_name):
        self.calls.append((user_id, tool_name))
        return True


def test_tool_executor_executes_light_pipeline_command():
    services = SimpleNamespace(
        quota=DummyQuota(),
        audit_logger=logging.getLogger("test.audit"),
    )

    executor = ToolExecutor(services=services)

    result = executor.execute_tool(
        "search_web",
        args={"query": "pinot"},
        user="u1",
    )

    assert result == {"results": ["Fake search result for 'pinot'"]}


def test_tool_executor_adds_user_to_args_when_missing(monkeypatch):
    from metis.tools import tool_executor as tool_executor_module

    captured = {}

    class DummyCommand:
        def execute(self, context):
            captured["args"] = context.args
            captured["user"] = context.user
            captured["services"] = context.services
            return "ok"

    monkeypatch.setitem(
        tool_executor_module.command_registry,
        "dummy_tool",
        lambda: DummyCommand(),
    )

    services = SimpleNamespace(
        quota=DummyQuota(),
        audit_logger=logging.getLogger("test.audit"),
    )

    executor = ToolExecutor(services=services)
    result = executor.execute_tool(
        "dummy_tool",
        args={"x": 1},
        user="u1",
    )

    assert result == "ok"
    assert captured["args"] == {"x": 1, "user": "u1"}
    assert captured["user"] == "u1"
    assert captured["services"] is services


def test_tool_executor_raises_for_unknown_tool():
    executor = ToolExecutor()

    with pytest.raises(ToolExecutionError):
        executor.execute_tool("missing_tool", args={})


def test_tool_executor_execute_alias_delegates():
    services = SimpleNamespace(
        quota=DummyQuota(),
        audit_logger=logging.getLogger("test.audit"),
    )

    executor = ToolExecutor(services=services)

    result = executor.execute(
        "search_web",
        args={"query": "merlot"},
        user="u1",
    )

    assert result == {"results": ["Fake search result for 'merlot'"]}