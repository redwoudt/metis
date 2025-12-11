import pytest
from metis.handlers.permissions import PermissionHandler
from metis.commands.base import ToolContext, ToolCommand


class DummyUser:
    def __init__(self, role):
        self.role = role


class DummyCmd(ToolCommand):
    name = "dummy"
    def execute(self, ctx): return "ok"


def test_permission_denied():
    handler = PermissionHandler()
    ctx = ToolContext(
        command=DummyCmd(),
        args={},
        user=DummyUser("guest"),
        metadata={"allow_user_tools": False}
    )

    with pytest.raises(PermissionError):
        handler.handle(ctx)


def test_permission_allows_admin():
    handler = PermissionHandler()
    ctx = ToolContext(
        command=DummyCmd(),
        args={},
        user=DummyUser("admin"),
        metadata={"allow_user_tools": False}
    )
    assert handler.handle(ctx) is ctx