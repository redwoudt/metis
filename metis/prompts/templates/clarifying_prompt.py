"""
Concrete prompt template for clarification tasks.
Used when the assistant needs to ask follow-up questions to better understand user input.
"""

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

class ClarifyingPrompt(BasePromptTemplate):
    """
    Builds a prompt to help the assistant clarify ambiguous or vague user input.
    """

    def __init__(self, context: str, tone: str = "Inquisitive", persona: str = "Curious Assistant"):
        super().__init__()
        self.context = context
        self.tone = tone
        self.persona = persona

    def set_tone(self):
        # Set tone and persona for seeking clarification
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        # Instruct the model to clarify the user's previous input
        self.prompt.task = "Ask clarifying questions to better understand the user's request."

    def inject_context(self):
        # Provide context that may be needed to frame clarification
        self.prompt.context = self.context

    def inject_tool_output(self):
        # No external tool output needed for clarification
        self.prompt.tool_output = ""