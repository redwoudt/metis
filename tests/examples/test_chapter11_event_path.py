from metis.examples.chapter11_event_path import main, run_demo


def test_chapter11_example_traces_one_correlated_event_path() -> None:
    result = run_demo()

    assert result == {
        "events_published": 3,
        "prompt.received_count": 1,
        "shared_correlation": True,
        "dispatch_continued": True,
    }


def test_chapter11_example_prints_a_stable_summary(capsys) -> None:
    assert main() == 0

    assert capsys.readouterr().out.splitlines() == [
        "events_published=3",
        "prompt.received_count=1",
        "shared_correlation=true",
        "dispatch_continued=true",
    ]
