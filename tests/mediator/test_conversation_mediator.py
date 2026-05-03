from metis.mediator import ConversationMediator, RequestContext


def test_prepare_context_creates_context():
    mediator = ConversationMediator()

    ctx = mediator.prepare_context("user1", "Hello world")

    assert isinstance(ctx, RequestContext)
    assert ctx.user_id == "user1"
    assert ctx.user_input == "Hello world"
    assert ctx.clean_input == "Hello world"


def test_handle_request_returns_placeholder():
    mediator = ConversationMediator()

    response = mediator.handle_request("user1", "Hello")

    assert "[Mediator placeholder]" in response
    assert "Hello" in response