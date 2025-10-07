# states/clarifying.py

from metis.states.base_state import ConversationState
import logging

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
        Generate a clarification prompt using preferences, call the model, and
        transition to ExecutingState. Return model response if available.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.executing import ExecutingState

        logger.debug("[ClarifyingState] Building prompt with user_input='%s', context='%s', tone='%s', persona='%s'",
                     user_input,
                     engine.preferences.get("context", ""),
                     engine.preferences.get("tone", ""),
                     engine.preferences.get("persona", ""))

        # Build the prompt
        prompt = render_prompt(
            prompt_type="clarifying",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        # Try rendering prompt string
        try:
            rendered_prompt = prompt.render() if hasattr(prompt, "render") else str(prompt)
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug("[ClarifyingState] Prompt constructed: %s", rendered_prompt)

        # Attempt to call the model
        model_response = None
        try:
            model = engine.get_model()
            if hasattr(model, "generate"):
                logger.debug("[ClarifyingState] Calling model.generate")
                model_response = model.generate(rendered_prompt)
                logger.debug("[ClarifyingState] Model response: %s", model_response)
            elif hasattr(model, "call"):
                logger.debug("[ClarifyingState] Calling model.call")
                model_response = model.call(rendered_prompt)
                logger.debug("[ClarifyingState] Model response: %s", model_response)
        except Exception as exc:
            logger.exception("[ClarifyingState] Model call failed: %s", exc)

        # Move to Executing state
        engine.set_state(ExecutingState())

        # Return model response if available, else return rendered prompt
        return model_response if model_response is not None else rendered_prompt