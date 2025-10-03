# states/greeting.py
# states/greeting.py

import logging
logger = logging.getLogger("metis.states.greeting")

from metis.states.base_state import ConversationState


class GreetingState(ConversationState):
    """
    The initial state of the conversation.
    Greets the user and transitions to ClarifyingState.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Respond with a greeting, call the model (if available) with the rendered prompt,
        and move to ClarifyingState. Return the model response if present; otherwise the
        rendered prompt string.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.clarifying import ClarifyingState

        # Build the prompt object/string
        logger.debug(
            f"[GreetingState] Building prompt with tone='{engine.preferences.get('tone', '')}', "
            f"persona='{engine.preferences.get('persona', '')}', context='{engine.preferences.get('context', '')}', "
            f"tool_output='{engine.preferences.get('tool_output', '')}', user_input='{user_input}'"
        )
        prompt = render_prompt(
            prompt_type="greeting",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        # Render prompt to string if the returned object supports .render()
        try:
            rendered_prompt = prompt.render() if hasattr(prompt, "render") else str(prompt)
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug(f"[GreetingState] Prompt constructed: {rendered_prompt}")

        # Try to call the model's generate method (or call if available).
        model_response = None
        try:
            model = engine.get_model()
            if hasattr(model, "generate"):
                logger.debug("[GreetingState] Calling model.generate")
                model_response = model.generate(rendered_prompt)
                logger.debug(f"[GreetingState] Model response: {model_response}")
            elif hasattr(model, "call"):
                logger.debug("[GreetingState] Calling model.call")
                model_response = model.call(rendered_prompt)
                logger.debug(f"[GreetingState] Model response: {model_response}")
        except Exception as exc:
            # Log but don't raise here; we still transition state and return prompt if model fails
            logger.exception("[GreetingState] Model call failed: %s", exc)

        # Transition to next state
        engine.set_state(ClarifyingState())

        # Prefer model response, fall back to rendered prompt
        return model_response if model_response is not None else rendered_prompt