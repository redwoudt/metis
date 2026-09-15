from metis.examples.chapter2_facade import run_example


def test_chapter2_example_uses_the_public_facade() -> None:
    outcome = run_example()

    assert outcome["entry_point"] == "RequestHandler"
    assert outcome["lifecycle_owner"] == "ConversationMediator"
    assert outcome["shared_services"] is True
    assert outcome["response_type"] == "str"


def test_chapter2_example_can_return_request_details() -> None:
    outcome = run_example(details=True)

    assert outcome["entry_point"] == "RequestHandler"
    assert outcome["lifecycle_owner"] == "ConversationMediator"
    assert outcome["shared_services"] is True
    assert outcome["response_type"] == "RequestResult"
    assert "one request entry point" in outcome["response"].lower()


def test_chapter2_example_leaves_no_session_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    run_example()

    assert not (tmp_path / "sessions.pkl").exists()
