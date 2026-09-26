from metis.examples.chapter12_mediator_workflow import main, run_demo


EXPECTED_SUMMARY = {
    "entry_point": "RequestHandler",
    "coordinator": "ConversationMediator",
    "response_returned": True,
    "session_tone": "concise",
    "one_completion_event": True,
    "session_persisted": True,
}


def test_chapter12_example_runs_one_mediated_request() -> None:
    assert run_demo() == EXPECTED_SUMMARY


def test_chapter12_example_prints_the_chapter_output(capsys) -> None:
    assert main() == 0

    assert capsys.readouterr().out.splitlines() == [
        "entry_point=RequestHandler",
        "coordinator=ConversationMediator",
        "response_returned=true",
        "session_tone=concise",
        "one_completion_event=true",
        "session_persisted=true",
    ]
