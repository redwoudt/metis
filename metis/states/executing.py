# states/executing.py

import logging
from typing import Any, Dict, Optional

from metis.states.base_state import ConversationState
from metis.config import Config


logger = logging.getLogger("metis.states.executing")


class ExecutingState(ConversationState):
    """
    Executes the confirmed user task using the Command + CoR tool pipeline.
    After execution, transitions to SummarizingState.
    """

    def __init__(self):
        super().__init__()

    # ----------------------------------------------------------------------
    # Public entrypoint
    # ----------------------------------------------------------------------
    def respond(self, engine, user_input: str) -> str:
        """
        Execute the selected tool (if any), produce a narration, and move to SummarizingState.
        """

        from metis.states.summarizing import SummarizingState

        self._ensure_preferences(engine)

        # Execute tool (or skip)
        tool_output = self._maybe_execute_tool(engine)

        # Build narration prompt
        prompt_text = self._build_execution_prompt(engine, user_input)

        # Call model for narration
        narration = self._call_model(engine, prompt_text)

        # Transition
        engine.set_state(SummarizingState())

        # Response priority: model narration → tool result → fallback
        return narration or f"Execution result: {tool_output or '[No output]'}"

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------

    def _ensure_preferences(self, engine) -> None:
        """Guarantees engine.preferences exists."""
        if not hasattr(engine, "preferences"):
            engine.preferences = {}

    def _maybe_execute_tool(self, engine) -> Optional[str]:
        """
        Executes tool if one was selected.
        Returns tool_output or None.
        """
        tool_name = engine.preferences.get("tool_name")
        tool_args = engine.preferences.get("tool_args", {})
        engine.preferences["tool_output"] = None

        if not tool_name:
            logger.info("[ExecutingState] No tool selected; skipping execution.")
            return None

        logger.info(f"[ExecutingState] Executing tool '{tool_name}' with args={tool_args}")

        try:
            services = Config.services()
            handler = engine.request_handler

            output = handler.execute_tool(
                tool_name=tool_name,
                args=tool_args,
                user=engine.user_id,
                services=services,
            )

            engine.preferences["tool_output"] = output
            return output

        except Exception as exc:
            logger.exception("[ExecutingState] Tool execution failed: %s", exc)
            failure_msg = f"Tool execution failed: {exc}"
            engine.preferences["tool_output"] = failure_msg
            return failure_msg

    def _build_execution_prompt(self, engine, user_input: str) -> str:
        """
        Renders the executing-state prompt safely.
        """
        from metis.services.prompt_service import render_prompt

        try:
            prompt = render_prompt(
                prompt_type="executing",
                user_input=user_input,
                context=engine.preferences.get("context", ""),
                tool_output=engine.preferences.get("tool_output", ""),
                tone=engine.preferences.get("tone", ""),
                persona=engine.preferences.get("persona", ""),
            )
            return prompt.render() if hasattr(prompt, "render") else str(prompt)

        except Exception as exc:
            logger.exception("[ExecutingState] Failed to build prompt: %s", exc)
            return f"Describe the result: {engine.preferences.get('tool_output', '')}"

    def _call_model(self, engine, prompt_text: str) -> Optional[str]:
        """
        Calls the model to generate narration. Returns None on failure.
        """
        try:
            logger.debug("[ExecutingState] Calling engine.generate_with_model")
            result = engine.generate_with_model(prompt_text)
            logger.debug("[ExecutingState] Model response received.")
            return result
        except Exception as exc:
            logger.exception("[ExecutingState] Model invocation failed: %s", exc)
            return None