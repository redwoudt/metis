import sys

from metis.examples.chapter16_template_strategy import main


def test_chapter16_example_reports_the_balanced_template(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["chapter16_template_strategy"])

    main()

    assert capsys.readouterr().out.splitlines() == [
        "template=balanced",
        "model_role=analysis",
        "response_style=default",
        "allow_tools=True",
        "safety=True",
        "citations=False",
    ]


def test_chapter16_example_applies_the_high_risk_override(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "chapter16_template_strategy",
            "--behavior",
            "balanced",
            "--risk",
            "high",
        ],
    )

    main()

    assert capsys.readouterr().out.splitlines() == [
        "template=safety-first",
        "model_role=analysis",
        "response_style=analytical",
        "allow_tools=False",
        "safety=True",
        "citations=True",
    ]

