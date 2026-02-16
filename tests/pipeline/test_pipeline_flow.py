# tests/pipeline/test_pipeline_flow.py

from metis.handlers.pipelines import build_light_pipeline, build_strict_pipeline
from metis.commands.base import ToolContext, ToolCommand


class DummyQuota:
    """
    Fake quota that always allows execution.
    """
    def allow(self, *_):
        return True


class DummyLogger:
    """
    Minimal audit logger stub.
    """
    def info(self, *_):
        pass


class DummyUser:
    """
    Minimal user object matching handler expectations.
    """
    def __init__(self, user_id):
        self.id = user_id
        self.role = "admin"


class DummyCmd(ToolCommand):
    name = "dummy"

    def execute(self, ctx):
        return "OK"


def test_light_pipeline_runs_all_handlers():
    """
    Light pipeline:
    - Validation
    - Execute
    (No permission / rate limit checks)
    """
    pipeline = build_light_pipeline()

    ctx = ToolContext(
        command=DummyCmd(),
        args={"a": 1},
        user=DummyUser("user_1"),
        metadata={},  # light pipeline ignores permissions but metadata must exist
    )

    out = pipeline.handle(ctx)
    assert out.result == "OK"


def test_strict_pipeline_runs_all_handlers():
    """
    Strict pipeline:
    - Validation
    - Permission
    - RateLimit
    - AuditLog
    - Execute
    """
    pipeline = build_strict_pipeline(DummyQuota(), DummyLogger())

    ctx = ToolContext(
        command=DummyCmd(),
        args={"a": 1},
        user=DummyUser("user_1"),
        metadata={
            # PermissionHandler expects this flag
            "allow_user_tools": True
        },
    )

    out = pipeline.handle(ctx)
    assert out.result == "OK"