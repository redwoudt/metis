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
            "[PlanPrompt] Initialized with tone='%s', persona='%s', context='%s', tool_output='%s'",
            tone, persona, context, tool_output
        )

    def set_tone(self):
        logger.debug("[PlanPrompt] Setting tone='%s', persona='%s'", self.tone, self.persona)
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        instruction = "Break down the user’s request into a step-by-step plan or set of recommendations."
        logger.debug("[PlanPrompt] Adding task instruction: '%s'", instruction)
        self.prompt.task = instruction

    def inject_context(self):
        logger.debug("[PlanPrompt] Injecting context: '%s'", self.context)
        self.prompt.context = self.context

    def inject_tool_output(self):
        logger.debug("[PlanPrompt] Injecting tool output: '%s'", self.tool_output)
        self.prompt.tool_output = self.tool_output