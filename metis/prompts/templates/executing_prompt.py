# metis/prompts/templates/executing_prompt.py

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

import logging

logger = logging.getLogger(__name__)


class ExecutingPrompt(BasePromptTemplate):
    """
    Prompt template for executing a user-defined task.
    Assembles a detailed instruction prompt using user input, context, and tool output.
    """

    def __init__(self, context="", tool_output="", tone="", persona=""):
        super().__init__(context, tool_output, tone, persona)
        logger.debug("[ExecutingPrompt] Initialized with context='%s', tool_output='%s', tone='%s', persona='%s'", context, tool_output, tone, persona)

    def add_task_instruction(self):
        self.prompt.task = "Execute the user-defined task using available tools or information."
        logger.debug("[ExecutingPrompt] Task set to: %s", self.prompt.task)

    def set_tone(self):
        self.prompt.tone = self.tone
        logger.debug("[ExecutingPrompt] Tone set to: %s", self.tone)

    def inject_context(self):
        logger.debug("[ExecutingPrompt] Injecting context")
        if self.context:
            self.prompt.context = self.context
            logger.debug("[ExecutingPrompt] Context set to: %s", self.context)

    def inject_tool_output(self):
        logger.debug("[ExecutingPrompt] Injecting tool output")
        if self.tool_output:
            self.prompt.tool_output = self.tool_output
            logger.debug("[ExecutingPrompt] Tool output set to: %s", self.tool_output)