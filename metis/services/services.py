import logging


class QuotaService:
    """
    Extremely simple quota/usage tracker for tool execution.
    In production this would plug into Redis or a persistent rate-limit system.
    """

    def __init__(self, limit_per_user: int = 100):
        self.limit_per_user = limit_per_user
        self.usage = {}  # user_id → count

    def allow(self, user_id: str, tool_name: str) -> bool:
        count = self.usage.get(user_id, 0)
        if count >= self.limit_per_user:
            return False
        self.usage[user_id] = count + 1
        return True


class Services:
    """
    Container that holds all backend services required by tool execution.
    Returned by Config.services().
    """

    def __init__(self):
        self.quota = QuotaService()
        self.audit_logger = logging.getLogger("metis.audit")


# SINGLETON INSTANCE
_services_singleton = Services()


def get_services() -> Services:
    """Return the shared services container."""
    return _services_singleton