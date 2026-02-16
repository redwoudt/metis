# metis/states/greeting.py

import logging

from metis.states.base_state import ConversationState

logger = logging.getLogger("metis.states.greeting")


class GreetingState(ConversationState):
    """
    The initial state of the conversation.
    Greets the user and transitions to ClarifyingState.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Respond with a greeting, call the model through the engine/bridge with the rendered
        prompt, and move to ClarifyingState. Return the model response if present;
        otherwise the rendered prompt string.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.clarifying import ClarifyingState

        # Ensure preferences exist
        if not hasattr(engine, "preferences") or engine.preferences is None:
            engine.preferences = {}

        logger.debug(
            "[GreetingState] Building prompt with tone='%s', persona='%s', context='%s', "
            "tool_output='%s', user_input='%s'",
            engine.preferences.get("tone", ""),
            engine.preferences.get("persona", ""),
            engine.preferences.get("context", ""),
            engine.preferences.get("tool_output", ""),
            user_input,
        )

        prompt = render_prompt(
            prompt_type="greeting",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", ""),
        )

        # Render prompt to string if the returned object supports .render()
        try:
            rendered_prompt = (
                prompt.render() if hasattr(prompt, "render") else str(prompt)
            )
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug("[GreetingState] Prompt constructed: %s", rendered_prompt)

        # Call the model via the engine's bridge hook
        model_response = None
        try:
            logger.debug("[GreetingState] Calling engine.generate_with_model")
            model_response = engine.generate_with_model(rendered_prompt)
            logger.debug("[GreetingState] Model response: %s", model_response)
        except Exception as exc:
            logger.exception(
                "[GreetingState] Model call via engine.generate_with_model failed: %s",
                exc,
            )

        # Move to the next state in the conversation
        engine.set_state(ClarifyingState())

        # Prefer model output; fall back to the rendered prompt
        return model_response if model_response is not None else rendered_prompt