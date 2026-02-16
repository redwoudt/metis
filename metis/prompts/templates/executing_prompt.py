# metis/prompts/templates/executing_prompt.py

import logging
from metis.prompts.templates.base_prompt_template import BasePromptTemplate

logger = logging.getLogger(__name__)


class ExecutingPrompt(BasePromptTemplate):
    """
    Prompt template used by ExecutingState to narrate tool execution results.
    Builds a prompt including user input, context, and tool output.
    """

    def __init__(self, tone="", persona="", context="", tool_output=""):
        # IMPORTANT: use named arguments to avoid ordering bugs
        super().__init__(
            tone=tone,
            persona=persona,
            context=context,
            tool_output=tool_output,
        )
        logger.debug(
            "[ExecutingPrompt] Initialized with tone='%s', persona='%s', context='%s', tool_output='%s'",
            tone,
            persona,
            context,
            tool_output,
        )

    def add_task_instruction(self):
        self.prompt.task = (
            "Explain what was executed and summarize the result clearly and briefly. "
            "If no tool was executed, state that and ask what to do next."
        )
        logger.debug("[ExecutingPrompt] Task set to: %s", self.prompt.task)

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