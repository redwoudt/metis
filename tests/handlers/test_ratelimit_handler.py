# tests/handlers/test_ratelimit_handler.py

import pytest
from metis.handlers.ratelimit import RateLimitHandler
from metis.commands.base import ToolContext, ToolCommand


class DummyQuota:
    """
    Fake quota implementation to control allow/deny behaviour
    deterministically in tests.
    """
    def __init__(self, allow=True):
        self._allow = allow

    def allow(self, user_id, tool_name):
        return self._allow


class DummyUser:
    """
    Minimal user object matching the refactored expectation:
    RateLimitHandler now accesses context.user.id
    """
    def __init__(self, user_id):
        self.id = user_id


class DummyCmd(ToolCommand):
    name = "dummy"

    def execute(self, ctx):
        return "ok"


def test_ratelimit_denies():
    """
    If the quota denies execution, RateLimitHandler should raise.
    """
    handler = RateLimitHandler(DummyQuota(allow=False))

    ctx = ToolContext(
        command=DummyCmd(),
        args={},
        user=DummyUser("user_1"),  # must expose `.id`
    )

    with pytest.raises(RuntimeError):
        handler.handle(ctx)


def test_ratelimit_allows():
    """
    If the quota allows execution, the context should pass through unchanged.
    """
    handler = RateLimitHandler(DummyQuota(allow=True))

    ctx = ToolContext(
        command=DummyCmd(),
        args={},
        user=DummyUser("user_1"),
    )

    assert handler.handle(ctx) is ctx