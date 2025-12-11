import pytest
from metis.commands.sql import ExecuteSQLCommand
from metis.commands.base import ToolContext


def test_execute_sql_runs_query(monkeypatch):
    cmd = ExecuteSQLCommand()

    # Mock DB exec
    fake_exec = lambda q: [{"result": "ok"}]
    monkeypatch.setattr(cmd, "_exec_query", fake_exec)

    ctx = ToolContext(
        command=cmd,
        args={"sql": "SELECT * FROM wines"},
        user="u1"
    )

    out = cmd.execute(ctx)
    assert "rows" in out
    assert out["rows"] == [{"result": "ok"}]


def test_execute_sql_rejects_missing_sql():
    cmd = ExecuteSQLCommand()
    ctx = ToolContext(command=cmd, args={}, user="u1")
    with pytest.raises(ValueError):
        cmd.execute(ctx)