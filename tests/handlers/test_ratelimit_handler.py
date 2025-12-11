import pytest
from metis.handlers.ratelimit import RateLimitHandler
from metis.commands.base import ToolContext, ToolCommand


class DummyQuota:
    def __init__(self, allow=True):
        self._allow = allow

    def allow(self, user_id, tool_name):
        return self._allow


class DummyCmd(ToolCommand):
    name = "dummy"
    def execute(self, ctx): return "ok"


def test_ratelimit_denies():
    handler = RateLimitHandler(DummyQuota(allow=False))
    ctx = ToolContext(command=DummyCmd(), args={}, user="u1")
    with pytest.raises(RuntimeError):
        handler.handle(ctx)


def test_ratelimit_allows():
    handler = RateLimitHandler(DummyQuota(allow=True))
    ctx = ToolContext(command=DummyCmd(), args={}, user="u1")
    assert handler.handle(ctx) is ctx