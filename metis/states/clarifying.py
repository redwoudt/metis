# states/clarifying.py

import logging
from metis.states.base_state import ConversationState

logger = logging.getLogger(__name__)


class ClarifyingState(ConversationState):
    """
    A state that confirms or refines the user's intent before taking action.
    Extracts tool name and arguments when present, and transitions to ExecutingState.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Build a clarification prompt, call the model, extract potential tool
        selection (tool name + arguments), then transition to ExecutingState.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.executing import ExecutingState

        # Ensure preferences exist
        if not hasattr(engine, "preferences"):
            engine.preferences = {}

        # -------------------------------------------------------------
        # 1. Build clarification prompt
        # -------------------------------------------------------------
        logger.debug(
            "[ClarifyingState] Building prompt with user_input='%s', context='%s', tone='%s', persona='%s'",
            user_input,
            engine.preferences.get("context", ""),
            engine.preferences.get("tone", ""),
            engine.preferences.get("persona", ""),
        )

        prompt = render_prompt(
            prompt_type="clarifying",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", ""),
        )

        try:
            rendered_prompt = (
                prompt.render() if hasattr(prompt, "render") else str(prompt)
            )
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug("[ClarifyingState] Prompt constructed: %s", rendered_prompt)

        # -------------------------------------------------------------
        # 2. Call the model to get clarification or structured output
        # -------------------------------------------------------------
        model_response = None
        try:
            logger.debug("[ClarifyingState] Calling engine.generate_with_model")
            model_response = engine.generate_with_model(rendered_prompt)
            logger.debug("[ClarifyingState] Model response: %s", model_response)
        except Exception as exc:
            logger.exception(
                "[ClarifyingState] Model call via engine.generate_with_model failed: %s",
                exc,
            )

        # Convert model response to text for inspection
        text_response = str(model_response) if model_response else ""

        # -------------------------------------------------------------
        # 3. Attempt to extract tool name + arguments
        # -------------------------------------------------------------
        # Pattern A: Model might return explicit structured JSON
        # Example:
        #   {"tool_call": {"name": "search_web", "arguments": {"query": "red wine"}}}
        tool_name = None
        tool_args = {}

        if isinstance(model_response, dict) and "tool_call" in model_response:
            tc = model_response["tool_call"]
            tool_name = tc.get("name")
            tool_args = tc.get("arguments", {})

        # Pattern B: Model returns text hinting at tool usage
        # Example: "Use search_web to find: red wine"
        # Simple heuristic — enhance later if needed
        if not tool_name:
            lower = text_response.lower()
            for name in engine.request_handler.config.get("tools", []):
                if name in lower:
                    tool_name = name
                    # naive arg extraction, can be improved
                    tool_args = {"input": user_input}
                    break

        # Pattern C: DSL pre-populated tool info in engine.preferences (no-op)

        # -------------------------------------------------------------
        # 4. Save tool decision into engine.preferences
        # -------------------------------------------------------------
        if tool_name:
            logger.info(
                f"[ClarifyingState] Selected tool '{tool_name}' with args={tool_args}"
            )
            engine.preferences["tool_name"] = tool_name
            engine.preferences["tool_args"] = tool_args

        # -------------------------------------------------------------
        # 5. Transition to ExecutingState
        # -------------------------------------------------------------
        engine.set_state(ExecutingState())

        # -------------------------------------------------------------
        # 6. Return model response or fallback to rendered prompt
        # -------------------------------------------------------------
        return model_response if model_response is not None else rendered_prompt