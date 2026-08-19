from metis.examples.chapter9_adaptive_responses import build_response


def test_analytical_style_sets_generation_parameters() -> None:
    parameters, response = build_response("analytical")

    assert parameters == {
        "temperature": 0.2,
        "max_tokens": 700,
    }
    assert response == "Odysseus chooses the clearest course home."


def test_decorators_are_applied_after_generation_in_composer_order() -> None:
    parameters, response = build_response(
        "concise",
        format_markdown=True,
        include_citations=True,
    )

    assert parameters == {"max_tokens": 120}
    assert response == (
        "## Response\n\n"
        "Odysseus chooses the clearest course home.\n\n"
        "Sources: [Model Generated]"
    )