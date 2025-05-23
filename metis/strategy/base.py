# Base PromptStrategy interface
from abc import ABC, abstractmethod

class PromptStrategy(ABC):
    @abstractmethod
    def build_prompt(self, session, user_input):
        pass
