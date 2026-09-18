import json

from metis.examples.chapter5_prompt_dsl import main, run_demo


def test_chapter5_example_reports_each_interpreter_stage() -> None:
    result = run_demo()

    assert result["tokens"][-1] == "EOF"
    assert result["expressions"] == [
        "PersonaExpr",
        "TaskExpr",
        "LengthExpr",
    ]
    assert result["context"] == {
        "persona": "Research Assistant",
        "task": "Summarize",
        "length": "3 bullet points",
    }
    assert "Task: Summarize" in result["prompt"]


def test_chapter5_example_cli_reports_success_and_validation_failure(
    capsys,
) -> None:
    assert main([]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["context"]["task"] == "Summarize"

    invalid = "[task: translate][length: 3 bullet points]"
    assert main(["--input", invalid]) == 2
    assert "ERROR=ValidationError:" in capsys.readouterr().err
