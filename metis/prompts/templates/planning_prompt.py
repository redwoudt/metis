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
        logger.debug(
            "[PlanningPrompt] Initialized tone_length=%d persona_length=%d "
            "context_length=%d tool_output_length=%d",
            len(tone or ""),
            len(persona or ""),
            len(context or ""),
            len(tool_output or ""),
        )

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
        logger.debug("[PlanningPrompt] Injecting context length=%d", len(self.context or ""))
        # Provide relevant session context or background
        self.prompt.context = self.context

    def inject_tool_output(self):
        logger.debug(
            "[PlanningPrompt] Injecting tool output length=%d",
            len(self.tool_output or ""),
        )
        # Include data from planning tools (e.g., schedules, constraints)
        self.prompt.tool_output = self.tool_output
