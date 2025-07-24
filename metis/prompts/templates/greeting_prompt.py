# metis/prompts/templates/greeting_prompt.py

from metis.prompts.templates.base_prompt_template import BasePromptTemplate


class GreetingPrompt(BasePromptTemplate):
    """
    Prompt template for generating a greeting message.
    Used at the start of a conversation to welcome and orient the user.
    """

    def add_task_instruction(self):
        self.prompt.task = "Generate a friendly greeting message to initiate the conversation."

    def set_tone(self):
        self.prompt.tone = self.tone

    def inject_context(self):
        if self.context:
            self.prompt.context = self.context

    def inject_tool_output(self):
        if self.tool_output:
            self.prompt.tool_output = self.tool_output