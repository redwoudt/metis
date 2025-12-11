from metis.handlers.auditlog import AuditLogHandler
from metis.commands.base import ToolContext, ToolCommand


class DummyLogger:
    def __init__(self):
        self.logged = []

    def info(self, msg):
        self.logged.append(msg)


class DummyCmd(ToolCommand):
    name = "dummy"
    def execute(self, ctx): return "ok"


def test_audit_log_records_action():
    audit = DummyLogger()
    handler = AuditLogHandler(audit)

    ctx = ToolContext(command=DummyCmd(), args={"a": 1}, user="u1")
    out = handler.handle(ctx)

    assert out is ctx
    assert any("dummy" in msg for msg in audit.logged)