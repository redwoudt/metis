"""
Concrete prompt template for planning tasks.
Includes tool output and specific planning-oriented instruction.
"""

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

class PlanningPrompt(BasePromptTemplate):
    """
    Builds a prompt to generate a step-by-step plan or strategy.
    """

    def __init__(self, context: str, tool_output: str, tone: str = "Encouraging", persona: str = "Step-by-Step Coach"):
        super().__init__()
        self.context = context
        self.tool_output = tool_output
        self.tone = tone
        self.persona = persona

    def set_tone(self):
        # Set tone and persona to match planning-oriented output
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        # Instruct the model to generate a plan from the context
        self.prompt.task = "Create a step-by-step plan based on the provided information."

    def inject_context(self):
        # Provide relevant session context or background
        self.prompt.context = self.context

    def inject_tool_output(self):
        # Include data from planning tools (e.g., schedules, constraints)
        self.prompt.tool_output = self.tool_output