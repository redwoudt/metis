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
            "[Prompt] render tone_length=%d persona_length=%d task_length=%d "
            "context_length=%d tool_output_length=%d input_length=%d",
            len(self.tone or ""),
            len(self.persona or ""),
            len(self.task or ""),
            len(self.context or ""),
            len(self.tool_output or ""),
            len(self.user_input or ""),
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
            logger.debug(
                "[Prompt] Added system message length=%d",
                len(system_message.strip()),
            )

        # Add task definition
        if self.task:
            messages.append(f"Task: {self.task}")
            logger.debug("[Prompt] Added task message length=%d", len(self.task))

        # Add session or scenario context
        if self.context:
            messages.append(f"Context: {self.context}")
            logger.debug("[Prompt] Added context message length=%d", len(self.context))

        # Add external tool result, if any
        if self.tool_output:
            messages.append(f"Tool Output: {self.tool_output}")
            logger.debug("[Prompt] Added tool output message length=%d", len(self.tool_output))

        # Add user input
        if self.user_input:
            messages.append(f"User Input: {self.user_input}")
            logger.debug("[Prompt] Added user input message length=%d", len(self.user_input))

        rendered = "\n".join(messages)
        logger.debug("[Prompt] Final rendered prompt length=%d", len(rendered))
        return rendered
