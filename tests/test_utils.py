from metis.strategy.base import PromptStrategy
from metis.policy.base import Policy


class MockPromptStrategy(PromptStrategy):
    def build_prompt(self, session, user_input):
        return f"[MockPrompt] {user_input}"


class AllowAllPolicy(Policy):
    def enforce(self, user_id, request):
        pass


class DenyAllPolicy(Policy):
    def enforce(self, user_id, request):
        raise PermissionError("Access Denied by Policy")
