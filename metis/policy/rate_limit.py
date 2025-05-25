"""
RateLimitPolicy restricts how many requests a user can make within a session.
"""

from metis.policy.base import Policy
from metis.config import Config


class RateLimitPolicy(Policy):
    def __init__(self):
        self.counter = {}

    def enforce(self, user_id, request):
        count = self.counter.get(user_id, 0)
        if count >= Config.RATE_LIMIT:
            raise PermissionError("Rate limit exceeded.")
        self.counter[user_id] = count + 1
