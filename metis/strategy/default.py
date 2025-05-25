"""
DefaultPromptStrategy builds a straightforward prompt using input text.

How it works:
- Simply appends user input to a default header.

Next Steps:
- Add support for basic task templating.
- Optionally enrich with recent context.
"""

from metis.strategy.base import PromptStrategy


class DefaultPromptStrategy(PromptStrategy):
    def build_prompt(self, session, user_input):
        return f"[DefaultPrompt]\n{user_input}"
