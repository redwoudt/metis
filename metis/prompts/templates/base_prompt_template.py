"""
Defines the BasePromptTemplate abstract class using the Template Method pattern.
Each subclass provides specific prompt task logic (e.g., summarization, planning).
"""

from abc import ABC, abstractmethod
from metis.prompts.prompt import Prompt


class BasePromptTemplate(ABC):
    """
    Base class for constructing a structured Prompt using the Template Method pattern.
    Subclasses override specific steps such as tone, task, context, and tool output.
    """

    def __init__(self, tone="Neutral", persona="Helpful Assistant", context="", tool_output=""):
        self.prompt = Prompt()
        self.tone = tone
        self.persona = persona
        self.context = context
        self.tool_output = tool_output

    def build_prompt(self, user_input: str) -> Prompt:
        """
        Template method: builds the prompt in a fixed sequence of steps.
        """
        self.set_tone_and_persona()
        self.add_task_instruction()
        self.inject_context()
        self.inject_tool_output()
        self.set_user_input(user_input)
        return self.prompt

    def set_tone_and_persona(self):
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def set_user_input(self, user_input: str):
        self.prompt.user_input = user_input

    @abstractmethod
    def add_task_instruction(self):
        """Subclasses should set the main task description for the prompt."""
        ...

    def inject_context(self):
        """Subclasses can override this to customize context injection."""
        self.prompt.context = self.context

    def inject_tool_output(self):
        """Subclasses can override this to customize tool output injection."""
        self.prompt.tool_output = self.tool_output