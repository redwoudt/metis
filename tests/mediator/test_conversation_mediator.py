from metis.mediator import ConversationMediator, RequestContext


class DummySessionManager:
    def load_or_create(self, user_id):
        raise AssertionError("load_or_create should not be called in this test")

    def save(self, user_id, session):
        raise AssertionError("save should not be called in this test")


def test_prepare_context_creates_context():
    mediator = ConversationMediator(session_manager=DummySessionManager())

    ctx = mediator.prepare_context("user1", "Hello world")

    assert isinstance(ctx, RequestContext)
    assert ctx.user_id == "user1"
    assert ctx.user_input == "Hello world"
    assert ctx.clean_input == "Hello world"
    assert ctx.correlation_id


def test_prepare_context_preserves_save_and_undo_flags():
    mediator = ConversationMediator(session_manager=DummySessionManager())

    ctx = mediator.prepare_context(
        user_id="user1",
        user_input="hello",
        save=True,
        undo=True,
    )

    assert ctx.save is True
    assert ctx.undo is True