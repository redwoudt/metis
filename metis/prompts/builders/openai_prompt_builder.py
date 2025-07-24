"""
OpenAIPromptBuilder formats a Prompt object using OpenAI's message format expectations.
Overrides the render method to match system/user style.
"""

from metis.prompts.prompt import Prompt
from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder

class OpenAIPromptBuilder(DefaultPromptBuilder):
    """
    A builder that constructs prompts using OpenAI-style roles and formatting.
    Inherits the default builder but overrides the final rendering behavior.
    """

    def build(self) -> Prompt:
        # Build the base prompt using parent builder logic
        prompt = super().build()

        # Override the render method with OpenAI message structure
        def openai_render():
            sections = []

            # System message includes tone and persona plus task and context
            system_parts = []
            if prompt.tone:
                system_parts.append(f"Tone: {prompt.tone}")
            if prompt.persona:
                system_parts.append(f"Persona: {prompt.persona}")
            if prompt.task:
                system_parts.append(f"Task: {prompt.task}")
            if prompt.context:
                system_parts.append(f"Context: {prompt.context}")
            if prompt.tool_output:
                system_parts.append(f"Tools: {prompt.tool_output}")

            system_message = "\n".join(system_parts)

            # Assemble OpenAI format
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt.user_input or ""}
            ]

            return messages

        # Patch the prompt's render method to return OpenAI-style message dict
        prompt.render = openai_render
        return prompt