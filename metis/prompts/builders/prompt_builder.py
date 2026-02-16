"""
PromptBuilder is responsible for creating structured, context-aware prompts for model input.
"""

import html
import re
import logging
from metis.prompts.prompt import Prompt
from metis.dsl import interpret_prompt_dsl, PromptContext

logger = logging.getLogger(__name__)


class PromptBuilder:
    def __init__(self, format_style="default"):
        self.format_style = format_style

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build(self, session, user_input: str) -> str:
        user_id = getattr(session, "user_id", "unknown")
        history = getattr(session, "history", [])
        user_input = self._sanitize(user_input)

        task = self._infer_task_type(user_input)

        logger.info(f"[PromptBuilder] build() user_id={user_id}, task={task}")

        header = f"[Session: {user_id}]"
        context = self._format_history(history)

        if self.format_style == "json":
            return self._format_json(user_id, history, user_input, task)

        return self._apply_task_template(task, header, context, user_input)

    def build_from_dsl(self, session, dsl_text: str) -> str:
        logger.info(f"[PromptBuilder] build_from_dsl() called")
        ctx: PromptContext = interpret_prompt_dsl(dsl_text)
        return self._apply_context_template(session, ctx)

    def build_prompt_from_dsl(self, session, dsl_text: str) -> Prompt:
        prompt_str = self.build_from_dsl(session, dsl_text)
        return Prompt(user_input=prompt_str)

    def build_prompt(self, session, user_input: str) -> Prompt:
        prompt_str = self.build(session, user_input)
        return Prompt(user_input=prompt_str)

    # ------------------------------------------------------------------
    # History handling (FIXED)
    # ------------------------------------------------------------------
    def _format_history(self, history) -> str:
        """
        Safely formats history entries.

        Supports:
        - legacy (prompt, response) tuples
        - message-like objects with .role / .content
        """
        if not history:
            return ""

        lines = []

        for entry in history[-3:]:
            # New message-style objects
            if hasattr(entry, "role") and hasattr(entry, "content"):
                role = entry.role.capitalize()
                content = self._sanitize(entry.content)
                lines.append(f"{role}: {content}")
                continue

            # Legacy tuple format: (prompt, response)
            if isinstance(entry, (tuple, list)) and len(entry) >= 2:
                user, system = entry[0], entry[1]
                lines.append(f"User: {self._sanitize(str(user))}")
                lines.append(f"System: {self._sanitize(str(system))}")
                continue

            # Fallback: stringify safely
            lines.append(f"Context: {self._sanitize(str(entry))}")

        formatted = "\n".join(lines)
        return f"\n\nPrevious interactions:\n{formatted}\n"

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _sanitize(self, text: str) -> str:
        text = (text or "").strip()
        text = html.escape(text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _infer_task_type(self, user_input: str) -> str:
        text = user_input.lower()
        if "summarize" in text:
            return "summarization"
        if "clarify" in text:
            return "clarifying"
        if "execute" in text:
            return "executing"
        if any(w in text for w in ("hi", "hello", "hey", "greetings")):
            return "greeting"
        return "general"

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    def _apply_context_template(self, session, ctx: PromptContext) -> str:
        user_id = getattr(session, "user_id", "unknown")
        history = getattr(session, "history", [])

        header = f"[Session: {user_id}]"
        context = self._format_history(history)

        parts = []
        for key in ("persona", "tone", "task", "source", "length", "format"):
            if ctx.get(key):
                parts.append(f"{key.capitalize()}: {self._sanitize(ctx[key])}")

        body = "\n".join(parts) if parts else "Current input:"
        return f"{header}{context}\n\n{body}"

    def _apply_task_template(self, task, header, context, user_input):
        if task == "summarization":
            return f"{header}{context}\n\nTask: Summarize the following input.\n{user_input}"
        if task == "clarifying":
            return f"{header}{context}\n\nTask: Clarify the following statement:\n{user_input}"
        if task == "executing":
            return f"{header}{context}\n\nTask: Execute the following instruction:\n{user_input}"
        if task == "greeting":
            return (
                f"{header}{context}\n\n"
                "Task: Generate a friendly greeting message.\n"
                f"{user_input}"
            )
        return f"{header}{context}\n\nCurrent input:\n{user_input}"

    def _format_json(self, user_id, history, user_input, task):
        context = []

        for entry in history[-3:]:
            if isinstance(entry, (tuple, list)) and len(entry) >= 2:
                context.append(
                    {
                        "user": self._sanitize(str(entry[0])),
                        "system": self._sanitize(str(entry[1])),
                    }
                )
            elif hasattr(entry, "role") and hasattr(entry, "content"):
                context.append(
                    {
                        entry.role.lower(): self._sanitize(entry.content)
                    }
                )

        return (
            "{\n"
            f'  "session": "{user_id}",\n'
            f'  "task": "{task}",\n'
            f'  "context": {context},\n'
            f'  "input": "{self._sanitize(user_input)}"\n'
            "}"
        )