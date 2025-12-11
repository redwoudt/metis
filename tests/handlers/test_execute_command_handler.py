from metis.handlers.execute import ExecuteCommandHandler
from metis.commands.base import ToolContext, ToolCommand


class DummyCmd(ToolCommand):
    name = "dummy"
    def execute(self, ctx): return "DONE"


def test_execute_handler_runs_command():
    handler = ExecuteCommandHandler()
    ctx = ToolContext(command=DummyCmd(), args={}, user="u1")

    out = handler.handle(ctx)
    assert ctx.result == "DONE"
    assert out is ctx