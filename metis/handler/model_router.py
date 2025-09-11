"""
model_router.py
---------------
Responsible for selecting the most appropriate model *role* for a given request,
based on context, DSL fields, and configuration.

This acts as a centralized decision point so that the rest of the system
can remain agnostic to which model or vendor is ultimately used.
The role returned here will be resolved by the ModelFactory.
"""

from typing import Optional
from metis.dsl import PromptContext

class ModelRouter:
    def __init__(self, default_role: str = "analysis", role_overrides: Optional[dict] = None):
        """
        :param default_role: Fallback role name if no other rules match.
        :param role_overrides: Optional mapping of task/persona keys to roles.
                               Example: {"summarize": "analysis", "poetry": "creative"}
        """
        self.default_role = default_role
        self.role_overrides = role_overrides or {}

    def route(self, ctx: Optional[PromptContext] = None, **kwargs) -> str:
        """
        Decide which model role to use.
        Priority:
          1. Explicit `role` in kwargs.
          2. Matching task/persona in overrides.
          3. Default role.
        :param ctx: Parsed PromptContext from DSL, if available.
        :param kwargs: Additional hint fields (e.g., task="summarize", persona="Analyst").
        :return: Selected model role (string).
        """
        # 1. Explicit role passed in kwargs
        explicit_role = kwargs.get("role")
        if explicit_role:
            return explicit_role

        # 2. Check for task/persona-specific overrides
        task = None
        persona = None
        if ctx:
            task = (ctx.get("task") or "").strip().lower()
            persona = (ctx.get("persona") or "").strip().lower()
        task = kwargs.get("task", task)
        persona = kwargs.get("persona", persona)

        if task and task in self.role_overrides:
            return self.role_overrides[task]
        if persona and persona in self.role_overrides:
            return self.role_overrides[persona]

        # 3. Fallback to default role
        return self.default_role

    def register_override(self, key: str, role_name: str) -> None:
        """
        Add or update a routing override.
        :param key: Task or persona keyword to match.
        :param role_name: Role name to use when key matches.
        """
        self.role_overrides[key.strip().lower()] = role_name

    def clear_overrides(self) -> None:
        """Remove all overrides."""
        self.role_overrides.clear()