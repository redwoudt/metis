# metis/prompts/templates/greeting_prompt.py
# metis/prompts/templates/greeting_prompt.py

import logging
logger = logging.getLogger(__name__)

from metis.prompts.templates.base_prompt_template import BasePromptTemplate


class GreetingPrompt(BasePromptTemplate):
    """
    Prompt template for generating a greeting message.
    Used at the start of a conversation to welcome and orient the user.
    """

    def __init__(self, context="", tool_output="", tone="", persona=""):
        super().__init__(
            tone=tone,
            persona=persona,
            context=context,
            tool_output=tool_output,
        )
        logger.debug(
            "GreetingPrompt initialized tone_length=%d persona_length=%d "
            "context_length=%d tool_output_length=%d",
            len(tone or ""),
            len(persona or ""),
            len(context or ""),
            len(tool_output or ""),
        )

    def add_task_instruction(self):
        logger.debug("Setting task instruction for GreetingPrompt")
        self.prompt.task = "Generate a friendly greeting message to initiate the conversation."

    def set_tone(self):
        logger.debug("Setting tone length=%d", len(self.tone or ""))
        self.prompt.tone = self.tone

    def inject_context(self):
        logger.debug("Injecting context into GreetingPrompt")
        if self.context:
            self.prompt.context = self.context

    def inject_tool_output(self):
        logger.debug("Injecting tool output into GreetingPrompt")
        if self.tool_output:
            self.prompt.tool_output = self.tool_output
