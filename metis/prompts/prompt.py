"""
Defines the Prompt data structure used by builders and templates to construct model-ready prompt strings.
Encapsulates tone, task, context, and user input with a render method.
"""

import logging

logger = logging.getLogger(__name__)

class Prompt:
    """
    Represents a structured prompt used by the GenAI system.
    Stores individual sections of the prompt and formats them on render.
    """

    def __init__(self, tone=None, persona=None, task=None, context=None, tool_output=None, user_input=None):
        self.tone = tone
        self.persona = persona
        self.task = task
        self.context = context
        self.tool_output = tool_output
        self.user_input = user_input

    def render(self) -> str:
        """
        Formats the prompt as a structured string, readable and informative to the model.
        """
        logger.debug(
            "[Prompt] Prompt.render called with tone=%r, persona=%r, task=%r, context=%r, tool_output=%r, user_input=%r",
            self.tone, self.persona, self.task, self.context, self.tool_output, self.user_input
        )
        messages = []

        # Add tone and persona as part of system message
        if self.tone or self.persona:
            system_message = ""
            if self.tone:
                system_message += f"[Tone: {self.tone}] "
            if self.persona:
                system_message += f"[Persona: {self.persona}]"
            messages.append(system_message.strip())
            logger.debug("[Prompt] Added system message: %r", system_message.strip())

        # Add task definition
        if self.task:
            messages.append(f"Task: {self.task}")
            logger.debug("[Prompt] Added task message: %r", f"Task: {self.task}")

        # Add session or scenario context
        if self.context:
            messages.append(f"Context: {self.context}")
            logger.debug("[Prompt] Added context message: %r", f"Context: {self.context}")

        # Add external tool result, if any
        if self.tool_output:
            messages.append(f"Tool Output: {self.tool_output}")
            logger.debug("[Prompt] Added tool output message: %r", f"Tool Output: {self.tool_output}")

        # Add user input
        if self.user_input:
            messages.append(f"User Input: {self.user_input}")
            logger.debug("[Prompt] Added user input message: %r", f"User Input: {self.user_input}")

        rendered = "\n".join(messages)
        logger.debug("[Prompt] Final rendered prompt: %r", rendered.replace("\n", "\\n"))
        return rendered