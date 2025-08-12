

"""
model_router.py
---------------
Responsible for selecting the most appropriate model or model provider
for a given request, based on context, DSL fields, and configuration.

This acts as a centralized decision point so that the rest of the system
can remain agnostic to which model is being used.
"""

from typing import Optional
from metis.dsl import PromptContext

class ModelRouter:
    def __init__(self, default_model: str = "gpt-4", model_overrides: Optional[dict] = None):
        """
        :param default_model: Name of the default model to use when no other rules match.
        :param model_overrides: Optional mapping of task/persona keys to model names.
                                Example: {"summarize": "gpt-4-32k", "code": "gpt-4-code"}
        """
        self.default_model = default_model
        self.model_overrides = model_overrides or {}

    def route(self, ctx: Optional[PromptContext] = None, **kwargs) -> str:
        """
        Decide which model to use.
        Priority:
          1. Explicit `model` in kwargs.
          2. Matching task/persona in overrides.
          3. Default model.
        :param ctx: Parsed PromptContext from DSL, if available.
        :param kwargs: Additional hint fields (e.g., task="summarize", persona="Analyst").
        :return: Selected model name (string).
        """
        # 1. Explicit model passed in kwargs
        explicit_model = kwargs.get("model")
        if explicit_model:
            return explicit_model

        # 2. Check for task/persona-specific overrides
        task = None
        persona = None
        if ctx:
            task = (ctx.get("task") or "").strip().lower()
            persona = (ctx.get("persona") or "").strip().lower()
        task = kwargs.get("task", task)
        persona = kwargs.get("persona", persona)

        if task and task in self.model_overrides:
            return self.model_overrides[task]
        if persona and persona in self.model_overrides:
            return self.model_overrides[persona]

        # 3. Fallback to default
        return self.default_model

    def register_override(self, key: str, model_name: str) -> None:
        """
        Add or update a routing override.
        :param key: Task or persona keyword to match.
        :param model_name: Model to use when key matches.
        """
        self.model_overrides[key.strip().lower()] = model_name

    def clear_overrides(self) -> None:
        """Remove all overrides."""
        self.model_overrides.clear()