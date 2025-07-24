"""
Defines the Prompt data structure used by builders and templates to construct model-ready prompt strings.
Encapsulates tone, task, context, and user input with a render method.
"""

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
        messages = []

        # Add tone and persona as part of system message
        if self.tone or self.persona:
            system_message = ""
            if self.tone:
                system_message += f"[Tone: {self.tone}] "
            if self.persona:
                system_message += f"[Persona: {self.persona}]"
            messages.append(system_message.strip())

        # Add task definition
        if self.task:
            messages.append(f"Task: {self.task}")

        # Add session or scenario context
        if self.context:
            messages.append(f"Context: {self.context}")

        # Add external tool result, if any
        if self.tool_output:
            messages.append(f"Tool Output: {self.tool_output}")

        # Add user input
        if self.user_input:
            messages.append(f"User Input: {self.user_input}")

        return "\n".join(messages)