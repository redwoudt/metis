# metis/prompts/templates/executing_prompt.py

from metis.prompts.templates.base_prompt_template import BasePromptTemplate


class ExecutingPrompt(BasePromptTemplate):
    """
    Prompt template for executing a user-defined task.
    Assembles a detailed instruction prompt using user input, context, and tool output.
    """

    def add_task_instruction(self):
        self.prompt.task = "Execute the user-defined task using available tools or information."

    def set_tone(self):
        self.prompt.tone = self.tone

    def inject_context(self):
        if self.context:
            self.prompt.context = self.context

    def inject_tool_output(self):
        if self.tool_output:
            self.prompt.tool_output = self.tool_output