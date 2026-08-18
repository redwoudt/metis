"""
Concrete prompt template for planning tasks.
Used when the assistant needs to help break down goals into actionable steps or a structured plan.
"""

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

import logging

logger = logging.getLogger(__name__)

class PlanPrompt(BasePromptTemplate):
    """
    Builds a prompt to help the assistant create a structured plan.
    """

    def __init__(self, context: str = "", tool_output: str = "", tone: str = "", persona: str = ""):
        super().__init__(tone, persona, context, tool_output)
        logger.debug(
            "[PlanPrompt] Initialized tone_length=%d persona_length=%d "
            "context_length=%d tool_output_length=%d",
            len(tone or ""),
            len(persona or ""),
            len(context or ""),
            len(tool_output or ""),
        )

    def set_tone(self):
        logger.debug(
            "[PlanPrompt] Setting tone_length=%d persona_length=%d",
            len(self.tone or ""),
            len(self.persona or ""),
        )
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        instruction = "Break down the user’s request into a step-by-step plan or set of recommendations."
        logger.debug("[PlanPrompt] Adding task instruction: '%s'", instruction)
        self.prompt.task = instruction

    def inject_context(self):
        logger.debug("[PlanPrompt] Injecting context length=%d", len(self.context or ""))
        self.prompt.context = self.context

    def inject_tool_output(self):
        logger.debug(
            "[PlanPrompt] Injecting tool output length=%d",
            len(self.tool_output or ""),
        )
        self.prompt.tool_output = self.tool_output
