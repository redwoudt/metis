"""
AuthPolicy ensures that only properly identified users can access the system.

How it works:
- Permits access to user IDs prefixed with "user_".

Next Steps:
- Support user roles, tokens, or JWT-based validation.
- Add user identity logging or multi-factor enforcement.
"""
from metis.policy.base import Policy

class AuthPolicy(Policy):
    def enforce(self, user_id, request):
        if not user_id.startswith("user_"):
            raise PermissionError("Invalid user authentication.")
