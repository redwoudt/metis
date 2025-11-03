# states/summarizing.py

import logging
from metis.states.base_state import ConversationState

logger = logging.getLogger("metis.states.summarizing")


class SummarizingState(ConversationState):
    """
    Summarizes the recent interaction or outcome.
    Resets the flow back to GreetingState for a new turn.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Provide a summary and loop back to GreetingState.

        :param engine: The conversation engine (context).
        :param user_input: Optional input triggering summary.
        :return: Summary message.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.greeting import GreetingState

        logger.debug(
            "[SummarizingState] Building prompt with tone='%s', persona='%s', context='%s', tool_output='%s', user_input='%s'",
            engine.preferences.get("tone", ""),
            engine.preferences.get("persona", ""),
            engine.preferences.get("context", ""),
            engine.preferences.get("tool_output", ""),
            user_input,
        )

        # Build a summarization prompt using the current context/preferences
        prompt = render_prompt(
            prompt_type="summarize",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", ""),
        )

        # Ensure we always have a string to send to the model
        try:
            rendered_prompt = prompt.render() if hasattr(prompt, "render") else str(prompt)
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug("[SummarizingState] Prompt constructed: %s", rendered_prompt)

        # Ask the model (through the Bridge path: ConversationEngine -> ModelManager -> Adapter)
        model_response = None
        try:
            logger.debug("[SummarizingState] Calling engine.generate_with_model")
            model_response = engine.generate_with_model(rendered_prompt)
            logger.debug("[SummarizingState] Model response: %s", model_response)
        except Exception as exc:
            logger.exception(
                "[SummarizingState] Model call via engine.generate_with_model failed: %s",
                exc,
            )

        # After summarizing, reset to GreetingState for the next interaction
        engine.set_state(GreetingState())

        # Final user-facing reply
        return f"Summary: {model_response or rendered_prompt}"