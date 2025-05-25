"""
Defines the PromptStrategy interface for generating prompts.

How it works:
- Provides an abstract base class with a required build_prompt method.

Next Steps:
- Add context-aware method contracts (e.g., token estimation).
- Define standard input/output prompt shapes.
"""
from abc import ABC, abstractmethod

class PromptStrategy(ABC):
    @abstractmethod
    def build_prompt(self, session, user_input):
        pass
