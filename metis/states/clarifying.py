# states/clarifying.py

import logging
from metis.states.base_state import ConversationState

logger = logging.getLogger(__name__)


class ClarifyingState(ConversationState):
    """
    A state that confirms or refines the user's intent before taking action.
    Transitions to ExecutingState once clarification is complete.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Generate a clarification prompt using preferences, call the model through
        the engine/bridge, then transition to ExecutingState.
        Return the model response if available, otherwise fall back to the rendered prompt.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.executing import ExecutingState

        logger.debug(
            "[ClarifyingState] Building prompt with user_input='%s', context='%s', tone='%s', persona='%s'",
            user_input,
            engine.preferences.get("context", ""),
            engine.preferences.get("tone", ""),
            engine.preferences.get("persona", "")
        )

        # Build a provider-agnostic prompt
        prompt = render_prompt(
            prompt_type="clarifying",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        # Convert prompt to a string (supporting objects with .render())
        try:
            rendered_prompt = prompt.render() if hasattr(prompt, "render") else str(prompt)
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug("[ClarifyingState] Prompt constructed: %s", rendered_prompt)

        # Call into the model via the Bridge path:
        # ConversationEngine -> ModelManager -> Adapter.
        model_response = None
        try:
            logger.debug("[ClarifyingState] Calling engine.generate_with_model")
            model_response = engine.generate_with_model(rendered_prompt)
            logger.debug("[ClarifyingState] Model response: %s", model_response)
        except Exception as exc:
            # Log but don't crash the conversation
            logger.exception(
                "[ClarifyingState] Model call via engine.generate_with_model failed: %s",
                exc,
            )

        # Advance to ExecutingState for the next turn
        engine.set_state(ExecutingState())

        # Prefer model output; fallback to rendered prompt
        return model_response if model_response is not None else rendered_prompt