from .validation import ValidationHandler
from .permissions import PermissionHandler
from .ratelimit import RateLimitHandler
from .audit import AuditLogHandler
from .execute import ExecuteCommandHandler


def build_light_pipeline():
    return ValidationHandler(
        ExecuteCommandHandler()
    )


def build_strict_pipeline(quota_service, audit_logger):
    return ValidationHandler(
        PermissionHandler(
            RateLimitHandler(
                quota_service,
                AuditLogHandler(
                    audit_logger,
                    ExecuteCommandHandler()
                )
            )
        )
    )