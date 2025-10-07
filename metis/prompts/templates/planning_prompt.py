"""
Concrete prompt template for planning tasks.
Includes tool output and specific planning-oriented instruction.
"""

import logging

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

logger = logging.getLogger(__name__)

class PlanningPrompt(BasePromptTemplate):
    """
    Builds a prompt to generate a step-by-step plan or strategy.
    """

    def __init__(self, context: str, tool_output: str, tone: str = "Encouraging", persona: str = "Step-by-Step Coach"):
        super().__init__(tone, persona, context, tool_output)
        logger.debug(f"[PlanningPrompt] Initialized with tone='{tone}', persona='{persona}', context='{context}', tool_output='{tool_output}'")

    def set_tone(self):
        logger.debug("[PlanningPrompt] Setting tone and persona")
        # Set tone and persona to match planning-oriented output
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        logger.debug("[PlanningPrompt] Adding task instruction")
        # Instruct the model to generate a plan from the context
        self.prompt.task = "Create a step-by-step plan based on the provided information."

    def inject_context(self):
        logger.debug(f"[PlanningPrompt] Injecting context: {self.context}")
        # Provide relevant session context or background
        self.prompt.context = self.context

    def inject_tool_output(self):
        logger.debug(f"[PlanningPrompt] Injecting tool output: {self.tool_output}")
        # Include data from planning tools (e.g., schedules, constraints)
        self.prompt.tool_output = self.tool_output