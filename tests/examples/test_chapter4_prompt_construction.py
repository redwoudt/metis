from metis.examples.chapter4_prompt_construction import (
    compare_prompt_paths,
    main,
)


def test_builder_and_template_produce_the_same_planning_prompt():
    builder_text, template_text = compare_prompt_paths(
        "Plan my interview preparation.",
        context="The interview is in two weeks.",
        tool_output="Calendar: five open study slots each week.",
    )

    assert builder_text == template_text
    assert "[Tone: Supportive] [Persona: Step-by-Step Coach]" in builder_text
    assert "Task: Create a step-by-step plan" in builder_text
    assert "Context: The interview is in two weeks." in builder_text
    assert "Tool Output: Calendar: five open study slots" in builder_text
    assert "User Input: Plan my interview preparation." in builder_text


def test_empty_tool_output_is_omitted_by_both_paths():
    builder_text, template_text = compare_prompt_paths(
        "Plan a three-day study sprint.",
        context="The exam is next Monday.",
        tool_output="",
        tone="Direct",
        persona="Study Coach",
    )

    assert builder_text == template_text
    assert "Tool Output:" not in builder_text


def test_cli_reports_that_the_paths_match(capsys):
    assert main([]) == 0

    output = capsys.readouterr().out
    assert "BUILDER" in output
    assert "TEMPLATE METHOD" in output
    assert output.rstrip().endswith("MATCH=True")
