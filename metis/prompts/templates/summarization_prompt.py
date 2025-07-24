"""
Concrete prompt template for summarization tasks.
Fills in tone, context, and a summarization instruction.
"""

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

class SummarizationPrompt(BasePromptTemplate):
    """
    Builds a prompt specifically for summarizing conversation or content.
    """

    def __init__(self, context: str, tool_output: str = "", tone: str = "Neutral", persona: str = "Concise Assistant"):
        super().__init__()
        self.context = context
        self.tool_output = tool_output
        self.tone = tone
        self.persona = persona

    def set_tone(self):
        # Set the tone and speaking persona for the assistant
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        # Instruct the model to perform a summarization task
        self.prompt.task = "Summarize the conversation clearly and briefly."

    def inject_context(self):
        # Include session memory or historical information
        self.prompt.context = self.context

    def inject_tool_output(self):
        # Summarization typically doesn't need tool output
        self.prompt.tool_output = ""