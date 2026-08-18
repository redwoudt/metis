"""
Concrete prompt template for clarification tasks.
Used when the assistant needs to ask follow-up questions to better understand user input.
"""

from metis.prompts.templates.base_prompt_template import BasePromptTemplate

import logging

logger = logging.getLogger(__name__)

class ClarifyingPrompt(BasePromptTemplate):
    """
    Builds a prompt to help the assistant clarify ambiguous or vague user input.
    """

    def __init__(self, context: str = "", tool_output: str = "", tone: str = "", persona: str = ""):
        super().__init__(tone, persona, context, tool_output)
        logger.debug(
            "[ClarifyingPrompt] Initialized tone_length=%d persona_length=%d "
            "context_length=%d tool_output_length=%d",
            len(tone or ""),
            len(persona or ""),
            len(context or ""),
            len(tool_output or ""),
        )

    def set_tone(self):
        logger.debug(
            "[ClarifyingPrompt] Setting tone_length=%d persona_length=%d",
            len(self.tone or ""),
            len(self.persona or ""),
        )
        # Set tone and persona for seeking clarification
        self.prompt.tone = self.tone
        self.prompt.persona = self.persona

    def add_task_instruction(self):
        logger.debug("[ClarifyingPrompt] Adding task instruction: '%s'", "Ask clarifying questions to better understand the user's request.")
        # Instruct the model to clarify the user's previous input
        self.prompt.task = "Ask clarifying questions to better understand the user's request."

    def inject_context(self):
        logger.debug("[ClarifyingPrompt] Injecting context length=%d", len(self.context or ""))
        # Provide context that may be needed to frame clarification
        self.prompt.context = self.context

    def inject_tool_output(self):
        logger.debug(
            "[ClarifyingPrompt] Injecting tool output length=%d",
            len(self.tool_output or ""),
        )
        # No external tool output needed for clarification
        self.prompt.tool_output = self.tool_output
