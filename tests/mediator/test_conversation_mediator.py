import pytest

from metis.dsl import ParseError
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


class DslSession:
    persona = ""
    tone = ""


def test_parse_dsl_uses_the_same_strict_interpreter_as_the_cli():
    mediator = ConversationMediator(session_manager=DummySessionManager())
    ctx = RequestContext(
        user_id="user1",
        user_input=(
            "[persona: Research Assistant][task: Summarize] Summarize this."
        ),
        session=DslSession(),
    )

    mediator.parse_dsl(ctx)

    assert ctx.dsl_context["persona"] == "Research Assistant"
    assert ctx.clean_input == "Summarize this."


def test_parse_dsl_rejects_malformed_leading_dsl():
    mediator = ConversationMediator(session_manager=DummySessionManager())
    ctx = RequestContext(
        user_id="user1",
        user_input="[task summarize] Summarize this.",
        session=DslSession(),
    )

    with pytest.raises(ParseError):
        mediator.parse_dsl(ctx)
