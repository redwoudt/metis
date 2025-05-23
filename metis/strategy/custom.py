# Example CustomPromptStrategy
from metis.strategy.base import PromptStrategy

class CustomPromptStrategy(PromptStrategy):
    def build_prompt(self, session, user_input):
        return f"Custom Strategy Used\nInput: {user_input}\nSession ID: {session['user_id']}"
