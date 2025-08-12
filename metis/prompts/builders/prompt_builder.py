"""
PromptBuilder is responsible for creating structured, context-aware prompts for model input.

How it works:
- Accepts user session data and new input.
- Infers task type from input (e.g., summarization, explanation, planning).
- Sanitizes input and history to remove unnecessary whitespace and escape HTML.
- Formats prompts using task-specific templates or JSON.
- Returns a clean, model-friendly prompt for downstream generation.

Expansion Ideas:
- Support for localization or multilingual prompt templates.
- Allow task overrides or manual task setting.
- Integrate prompt validation and token estimation.
- Add templates for new task types (e.g., classification, code generation).
- Enable prompt versioning for A/B testing or tuning.
"""

import html
import re
from metis.prompts.prompt import Prompt
from metis.dsl import interpret_prompt_dsl, PromptContext


class PromptBuilder:
    def __init__(self, format_style="default"):
        self.format_style = format_style

    def build(self, session, user_input: str) -> str:
        user_id = getattr(session, "user_id", "unknown")
        history = getattr(session, "history", [])
        user_input = self._sanitize(user_input)

        # Infer task type
        task = self._infer_task_type(user_input)

        # Format session header and history
        header = f"[Session: {user_id}]"
        if history:
            formatted_history = "\n".join(
                f"User: {self._sanitize(prompt)}\nSystem: {self._sanitize(response)}"
                for prompt, response in history[-3:]
            )
            context = f"\n\nPrevious interactions:\n{formatted_history}\n"
        else:
            context = ""

        # Format prompt
        if self.format_style == "json":
            return self._format_json(user_id, history, user_input, task)
        else:
            return self._apply_task_template(task, header, context, user_input)

    def build_from_dsl(self, session, dsl_text: str) -> str:
        """
        Parse [key: value] blocks using the DSL interpreter and return a formatted prompt string.
        Does not break existing callers that use plain text.
        """
        ctx: PromptContext = interpret_prompt_dsl(dsl_text)
        return self._apply_context_template(session, ctx)

    def build_prompt_from_dsl(self, session, dsl_text: str) -> Prompt:
        """
        Convenience: build a Prompt object directly from DSL input.
        """
        prompt_str = self.build_from_dsl(session, dsl_text)
        return Prompt(user_input=prompt_str)

    def build_prompt(self, session, user_input: str) -> Prompt:
        """
        Converts legacy string-based prompt into a Prompt object for compatibility with new system.
        """
        prompt_str = self.build(session, user_input)
        return Prompt(user_input=prompt_str)

    def _sanitize(self, text: str) -> str:
        text = text.strip()
        text = html.escape(text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _infer_task_type(self, user_input: str) -> str:
        text = user_input.lower()
        if "summarize" in text:
            return "summarization"
        elif "explain" in text:
            return "explanation"
        elif "plan" in text:
            return "planning"
        return "general"

    def _apply_context_template(self, session, ctx: PromptContext) -> str:
        user_id = getattr(session, "user_id", "unknown")
        history = getattr(session, "history", [])

        header = f"[Session: {user_id}]"
        if history:
            formatted_history = "\n".join(
                f"User: {self._sanitize(prompt)}\nSystem: {self._sanitize(response)}"
                for prompt, response in history[-3:]
            )
            context = f"\n\nPrevious interactions:\n{formatted_history}\n"
        else:
            context = ""

        # Map DSL fields into a friendly body similar to existing templates
        parts = []
        if ctx.get("persona"):
            parts.append(f"Persona: {self._sanitize(ctx['persona'])}")
        if ctx.get("tone"):
            parts.append(f"Tone: {self._sanitize(ctx['tone'])}")
        if ctx.get("task"):
            parts.append(f"Task: {self._sanitize(ctx['task'])}")
        if ctx.get("source"):
            parts.append(f"Source: {self._sanitize(ctx['source'])}")
        if ctx.get("length"):
            parts.append(f"Length: {self._sanitize(ctx['length'])}")
        if ctx.get("format"):
            parts.append(f"Format: {self._sanitize(ctx['format'])}")

        body = "\n".join(parts) if parts else "Current input:"
        return f"{header}{context}\n\n{body}"

    def _apply_task_template(self, task, header, context, user_input):
        if task == "summarization":
            return f"{header}{context}\n\nTask: Summarize the following input.\n{user_input}"
        elif task == "explanation":
            return f"{header}{context}\n\nTask: Provide a clear explanation for:\n{user_input}"
        elif task == "planning":
            return f"{header}{context}\n\nTask: Create a detailed plan based on:\n{user_input}"
        return f"{header}{context}\n\nCurrent input:\n{user_input}"

    def _format_json(self, user_id, history, user_input, task):
        context = [
            {"user": self._sanitize(p), "system": self._sanitize(r)}
            for p, r in history[-3:]
        ]
        return (
            f'{{\n  "session": "{user_id}",\n  '
            f'"task": "{task}",\n  "context": {context},\n  '
            f'"input": "{self._sanitize(user_input)}"\n}}'
        )