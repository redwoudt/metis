import pytest
from metis.handlers.validation import ValidationHandler
from metis.commands.base import ToolContext, ToolCommand


class DummyCmd(ToolCommand):
    name = "dummy"
    def execute(self, ctx): return "ok"


def test_validation_passes_valid_args():
    handler = ValidationHandler()
    ctx = ToolContext(command=DummyCmd(), args={"x": 1}, user="u1")
    out = handler.handle(ctx)
    assert out is ctx


def test_validation_fails_missing_required_arg():
    handler = ValidationHandler()
    ctx = ToolContext(command=DummyCmd(), args={"x": None}, user="u1")
    with pytest.raises(ValueError):
        handler.handle(ctx)