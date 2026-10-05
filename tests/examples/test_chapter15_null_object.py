import sys

import pytest

from metis.examples.chapter15_null_object import main


@pytest.mark.parametrize(
    ("mode", "publisher", "events"),
    [
        ("omitted", "NullEventPublisher", 0),
        ("null", "NullEventPublisher", 0),
        ("real", "EventBus", 2),
    ],
)
def test_chapter15_example_completes_with_each_publisher(
    monkeypatch,
    capsys,
    mode: str,
    publisher: str,
    events: int,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["chapter15_null_object", "--publisher", mode],
    )

    main()

    assert capsys.readouterr().out.splitlines() == [
        f"Configuration: {mode}",
        f"Publisher: {publisher}",
        f"Events captured: {events}",
        "Response: [mock:chapter-15] Continue",
        "Core request: complete",
    ]

