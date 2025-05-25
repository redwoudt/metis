from metis.components.session_manager import SessionManager


def test_session_manager_lifecycle():
    manager = SessionManager()
    session = manager.load_or_create("user_123")
    assert session["user_id"] == "user_123"

    manager.save("user_123", session, "prompt", "response")
    assert ("prompt", "response") in session["history"]
