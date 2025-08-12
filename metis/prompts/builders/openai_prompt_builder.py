"""
OpenAIPromptBuilder formats a Prompt object using OpenAI's message format expectations.
Overrides the render method to match system/user style.
"""

from metis.prompts.prompt import Prompt
from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder
from metis.dsl import interpret_prompt_dsl, PromptContext

class OpenAIPromptBuilder(DefaultPromptBuilder):
    """
    A builder that constructs prompts using OpenAI-style roles and formatting.
    Inherits the default builder but overrides the final rendering behavior.
    """

    def _patch_openai_render(self, prompt: Prompt) -> Prompt:
        """
        Replace the prompt.render with an OpenAI-style messages renderer.
        """
        def openai_render():
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
        prompt.render = openai_render
        return prompt

    def build_from_dsl(self, dsl_text: str) -> Prompt:
        """
        Parse [key: value] prompt blocks with the DSL and build an OpenAI-formatted Prompt.
        """
        ctx: PromptContext = interpret_prompt_dsl(dsl_text)
        # Let DefaultPromptBuilder map ctx → Prompt fields
        super().build_with_context(ctx)
        # Now return a Prompt with OpenAI-style render function
        prompt = super().build()
        return self._patch_openai_render(prompt)

    def build(self) -> Prompt:
        # Build the base prompt using parent builder logic
        prompt = super().build()

        # Patch the prompt's render method to return OpenAI-style message dict
        return self._patch_openai_render(prompt)