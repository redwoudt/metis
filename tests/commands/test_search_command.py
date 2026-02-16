import pytest
from metis.commands.search import SearchWebCommand
from metis.commands.base import ToolContext


def test_search_web_executes():
    cmd = SearchWebCommand()
    ctx = ToolContext(command=cmd, args={"query": "red wine"}, user="u1")
    out = cmd.execute(ctx)

    assert isinstance(out, dict)
    assert "results" in out
    assert isinstance(out["results"], list)


def test_search_web_missing_query():
    cmd = SearchWebCommand()
    ctx = ToolContext(command=cmd, args={}, user="u1")

    with pytest.raises(ValueError):
        cmd.execute(ctx)