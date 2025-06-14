"""
Tests for SessionManager lifecycle and memory persistence.
"""

from metis.components.session_manager import SessionManager


def test_session_creation_and_retrieval():
    manager = SessionManager()
    session = manager.load_or_create("user_test")
    assert session.user_id == "user_test"


def test_session_history_append():
    manager = SessionManager()
    session = manager.load_or_create("user_test")
    manager.save("user_test", session, "prompt", "response")
    assert ("prompt", "response") in session.history


def test_session_idempotency():
    manager = SessionManager()
    s1 = manager.load_or_create("user_id")
    s2 = manager.load_or_create("user_id")
    assert s1 is s2
