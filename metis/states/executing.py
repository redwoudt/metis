# states/executing.py

import logging
logger = logging.getLogger("metis.states.executing")

from metis.states.base_state import ConversationState


class ExecutingState(ConversationState):
    """
    Executes the confirmed user task using available tools or logic.
    Transitions to SummarizingState after execution.
    """

    def __init__(self):
        super().__init__()

    def respond(self, engine, user_input):
        """
        Build an execution-ready prompt, call the model (through the bridge),
        and then move to summarization.

        :param engine: The conversation engine (context).
        :param user_input: The user's confirmed instruction.
        :return: Model response or fallback simulated response.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.summarizing import SummarizingState

        logger.debug(
            "[ExecutingState] Building prompt with tone='%s', persona='%s', context='%s', "
            "tool_output='%s', user_input='%s'",
            engine.preferences.get("tone", ""),
            engine.preferences.get("persona", ""),
            engine.preferences.get("context", ""),
            engine.preferences.get("tool_output", ""),
            user_input,
        )

        # Build provider-agnostic execution prompt using our prompt builder pipeline
        prompt = render_prompt(
            prompt_type="executing",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        # Make sure we always have a string to send to the model
        try:
            rendered_prompt = prompt.render() if hasattr(prompt, "render") else str(prompt)
        except Exception:
            rendered_prompt = str(prompt)

        logger.debug("[ExecutingState] Prompt constructed: %s", rendered_prompt)

        # Call the model through the Bridge path:
        # ConversationEngine -> ModelManager -> Adapter.
        model_response = None
        try:
            logger.debug("[ExecutingState] Calling engine.generate_with_model")
            model_response = engine.generate_with_model(rendered_prompt)
            logger.debug("[ExecutingState] Model response: %s", model_response)
        except Exception as exc:
            # We don't kill the flow if the provider call fails;
            # SummarizingState should still run to close the loop.
            logger.exception(
                "[ExecutingState] Model call via engine.generate_with_model failed: %s",
                exc,
            )

        # Move to the next phase of the conversation: summarizing what just happened
        engine.set_state(SummarizingState())

        # Prefer the model output; fall back to a synthesized execution message
        return model_response if model_response is not None else f"Executing task: {rendered_prompt}"