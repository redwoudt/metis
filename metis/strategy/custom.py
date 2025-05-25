"""
CustomPromptStrategy allows developers to test or override prompt-building behavior.

How it works:
- Embeds session and input info in a custom structure.

Next Steps:
- Add support for custom formatting rules or plug-ins.
"""
from metis.strategy.base import PromptStrategy

class CustomPromptStrategy(PromptStrategy):
    def build_prompt(self, session, user_input):
        return f"Custom Strategy Used\nInput: {user_input}\nSession ID: {session['user_id']}"
