from metis.mediator import RequestContext


def test_request_context_initialization():
    ctx = RequestContext(user_id="user1", user_input="Hello")

    assert ctx.user_id == "user1"
    assert ctx.user_input == "Hello"
    assert ctx.clean_input == ""
    assert isinstance(ctx.dsl_context, dict)
    assert ctx.tool_name is None
    assert ctx.response == ""
    assert ctx.correlation_id is not None


def test_request_context_defaults():
    ctx = RequestContext(user_id="u", user_input="hi")

    assert ctx.dsl_context == {}
    assert ctx.tool_args == {}
    assert ctx.model_role == "analysis"