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


class PromptBuilder:
    def __init__(self, format_style="default"):
        self.format_style = format_style

    def build(self, session, user_input: str) -> str:
        user_id = session.get("user_id", "unknown")
        history = session.get("history", [])
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
