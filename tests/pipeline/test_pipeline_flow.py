from metis.handlers.pipelines import build_light_pipeline, build_strict_pipeline
from metis.commands.base import ToolContext, ToolCommand


class DummyQuota:
    def allow(self, *_): return True


class DummyLogger:
    def info(self, *_): pass


class DummyCmd(ToolCommand):
    name = "dummy"
    def execute(self, ctx): return "OK"


def test_light_pipeline_runs_all_handlers():
    pipeline = build_light_pipeline()
    ctx = ToolContext(command=DummyCmd(), args={"a": 1}, user="u1")

    out = pipeline.handle(ctx)
    assert out.result == "OK"


def test_strict_pipeline_runs_all_handlers():
    pipeline = build_strict_pipeline(DummyQuota(), DummyLogger())
    ctx = ToolContext(command=DummyCmd(), args={"a": 1}, user="u1")

    out = pipeline.handle(ctx)
    assert out.result == "OK"