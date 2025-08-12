# tests/integration/test_prompt_flow_with_dsl.py

import pytest

def test_dsl_full_prompt_flow_via_request_handler():
    """
    End-to-end: DSL in user_input -> RequestHandler -> routed state/model -> engine.respond.
    """
    from metis.handler.request_handler import RequestHandler

    handler = RequestHandler()
    user_id = "user_dsl_1"
    user_input = (
        "[persona: Research Assistant]"
        "[tone: optimistic]"
        "[task: summarize]"
        "[length: 3 bullet points]"
        " Please summarize our discussion about onboarding."
    )

    response = handler.handle_prompt(user_id=user_id, user_input=user_input, save=False, undo=False)

    assert isinstance(response, str)
    # We expect either the task or the subject to appear in the response
    assert "summarize" in response.lower() or "onboarding" in response.lower()


def test_dsl_smoke_with_builder_and_engine():
    """
    Lightweight smoke test: Interpreter -> DefaultPromptBuilder -> ConversationEngine.
    Useful if RequestHandler evolves independently, but we still want DSL coverage.
    """
    from metis.dsl import interpret_prompt_dsl
    from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder
    from metis.prompts.prompt import Prompt
    from metis.conversation_engine import ConversationEngine

    dsl_text = (
        "[persona: Analyst]"
        "[tone: neutral]"
        "[task: summarize]"
        "[format: bullets]"
        "[length: short]"
    )
    ctx = interpret_prompt_dsl(dsl_text)

    builder = DefaultPromptBuilder()
    prompt_obj: Prompt = builder.build_with_context(ctx)
    # Provide the actual user input we want summarized
    prompt_obj.user_input = "Summarize the quarterly results focusing on ARR and churn."

    engine = ConversationEngine()
    response = engine.respond(prompt_obj.render() if callable(getattr(prompt_obj, "render", None)) else str(prompt_obj))

    assert isinstance(response, str)
    assert "arr" in response.lower() or "churn" in response.lower()