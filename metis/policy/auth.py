# AuthPolicy implementation
from metis.policy.base import Policy

class AuthPolicy(Policy):
    def enforce(self, user_id, request):
        if not user_id.startswith("user_"):
            raise PermissionError("Invalid user authentication.")
