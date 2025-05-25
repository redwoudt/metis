"""
Policy module encapsulating enforcement logic such as rate limits and authentication.

How it works:
- Centralizes access control and usage governance.
- Exposes interface and default implementations.

Next Steps:
- Introduce tiered rate limits, org roles, or time-based controls.
- Extend with logging and audit tracking.
"""

from .base import Policy
from .rate_limit import RateLimitPolicy
from .auth import AuthPolicy
