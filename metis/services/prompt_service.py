"""
Orchestrates prompt construction using builder or template classes.
Acts as the interface between higher-level components (e.g. ConversationEngine) and prompt logic.
"""

from metis.prompts.templates.greeting_prompt import GreetingPrompt
from metis.prompts.templates.executing_prompt import ExecutingPrompt
from metis.prompts.templates.summarization_prompt import SummarizationPrompt
from metis.prompts.templates.planning_prompt import PlanningPrompt
from metis.prompts.templates.clarifying_prompt import ClarifyingPrompt
from metis.prompts.templates.critique_prompt import CritiquePrompt
from metis.prompts.prompt import Prompt

import logging
logger = logging.getLogger(__name__)

# Optional: support different prompt strategies from one place
TEMPLATE_MAP = {
    "greeting": GreetingPrompt,
    "executing": ExecutingPrompt,
    "summarize": SummarizationPrompt,
    "plan": PlanningPrompt,
    "clarifying": ClarifyingPrompt,
    "critique": CritiquePrompt,
}

def generate_prompt(prompt_type: str, user_input: str, context: str = "", tool_output: str = "", tone: str = "", persona: str = "") -> Prompt:
    """
    Entry point for generating a prompt object based on a known prompt_type.
    Returns a fully constructed Prompt object.
    """
    # Fallback to neutral tone/persona if not provided
    tone = tone or "Neutral"
    persona = persona or "Helpful Assistant"

    # Select the appropriate prompt template class
    prompt_cls = TEMPLATE_MAP.get(prompt_type)
    if not prompt_cls:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    # Instantiate the prompt template with appropriate values
    template = prompt_cls(
        context=context,
        tool_output=tool_output,
        tone=tone,
        persona=persona
    )

    # Build and return the prompt object
    prompt_obj = template.build_prompt(user_input)
    logger.debug(f"[generate_prompt] Created prompt: {template}")
    return prompt_obj

def render_prompt(prompt_type: str, user_input: str, context: str = "", tool_output: str = "", tone: str = "", persona: str = "") -> str:
    """
    Wrapper that generates and returns the final rendered prompt string.
    """
    prompt = generate_prompt(
        prompt_type=prompt_type,
        user_input=user_input,
        context=context,
        tool_output=tool_output,
        tone=tone,
        persona=persona
    )
    rendered = prompt.render()
    logger.debug(f"[render_prompt] Final rendered prompt: {rendered}")
    return rendered

class PromptFormatter:
    """
    Utility for applying custom formatting rules to prompt content.
    Can be extended for token limits, formatting normalization, etc.
    """

    @staticmethod
    def truncate(prompt: Prompt, max_tokens: int = 2048) -> Prompt:
        """
        Naive truncation: trims context and tool_output if too long.
        """
        if len(prompt.context) > max_tokens // 2:
            prompt.context = prompt.context[:max_tokens // 2]
        if len(prompt.tool_output) > max_tokens // 2:
            prompt.tool_output = prompt.tool_output[:max_tokens // 2]
        return prompt

    @staticmethod
    def normalize_whitespace(prompt: Prompt) -> Prompt:
        """
        Strips excessive whitespace from prompt fields.
        """
        prompt.task = prompt.task.strip()
        prompt.context = prompt.context.strip()
        prompt.tool_output = prompt.tool_output.strip()
        prompt.user_input = prompt.user_input.strip()
        return prompt