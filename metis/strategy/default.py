# DefaultPromptStrategy implementation
from metis.strategy.base import PromptStrategy

class DefaultPromptStrategy(PromptStrategy):
    def build_prompt(self, session, user_input):
        return f"DefaultPrompt: {user_input}"
