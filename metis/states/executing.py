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
        Build an execution-ready prompt, call the model to perform the task, and move to summarization.

        :param engine: The conversation engine (context).
        :param user_input: The user's confirmed instruction.
        :return: Model response or fallback simulated response.
        """
        from metis.services.prompt_service import render_prompt
        from metis.states.summarizing import SummarizingState

        logger.debug(f"[ExecutingState] Building prompt with tone='{engine.preferences.get('tone', '')}', "
                     f"persona='{engine.preferences.get('persona', '')}', context='{engine.preferences.get('context', '')}', "
                     f"tool_output='{engine.preferences.get('tool_output', '')}', user_input='{user_input}'")

        # Use new Builder + Template Method–based system to construct prompt
        prompt = render_prompt(
            prompt_type="executing",
            user_input=user_input,
            context=engine.preferences.get("context", ""),
            tool_output=engine.preferences.get("tool_output", ""),
            tone=engine.preferences.get("tone", ""),
            persona=engine.preferences.get("persona", "")
        )

        logger.debug(f"[ExecutingState] Prompt constructed: {prompt}")

        # Call the model to execute the task
        model_response = None
        try:
            model = engine.get_model()
            if hasattr(model, "generate"):
                logger.debug("[ExecutingState] Calling model.generate")
                model_response = model.generate(prompt)
                logger.debug("[ExecutingState] Model response: %s", model_response)
            elif hasattr(model, "call"):
                logger.debug("[ExecutingState] Calling model.call")
                model_response = model.call(prompt)
                logger.debug("[ExecutingState] Model response: %s", model_response)
        except Exception as exc:
            logger.exception("[ExecutingState] Model call failed: %s", exc)

        # Transition to next state
        engine.set_state(SummarizingState())

        return model_response if model_response is not None else f"Executing task: {prompt}"