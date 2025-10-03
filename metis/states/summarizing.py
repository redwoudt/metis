# states/summarizing.py

from metis.states.base_state import ConversationState
import logging

logger = logging.getLogger("metis.states.greeting")


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

        prompt = render_prompt(
            prompt_type="summarize",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", ""),
        )
        logger.debug("[SummarizingState] Prompt constructed: %s", prompt)

        # Try calling the model to generate the summary
        model_response = None
        try:
            model = engine.get_model()
            if hasattr(model, "generate"):
                logger.debug("[SummarizingState] Calling model.generate")
                model_response = model.generate(prompt)
                logger.debug("[SummarizingState] Model response: %s", model_response)
            elif hasattr(model, "call"):
                logger.debug("[SummarizingState] Calling model.call")
                model_response = model.call(prompt)
                logger.debug("[SummarizingState] Model response: %s", model_response)
        except Exception as exc:
            logger.exception("[SummarizingState] Model call failed: %s", exc)

        engine.set_state(GreetingState())
        return f"Summary: {model_response or prompt}"