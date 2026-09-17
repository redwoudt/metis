import subprocess
import sys
import os
import json
import pytest

CLI_PATH = os.path.join("metis", "tools", "metis_cli.py")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


@pytest.mark.parametrize("args,expect", [
    (["prompt", "--type", "summarize", "--input", "Summarize this message"], "Summarize this message"),
    (["prompt", "--type", "plan", "--input", "Plan my project", "--context", "Week schedule"], "Plan my project"),
])
def test_prompt_cli_invokes_successfully(args, expect):
    result = subprocess.run(
        [sys.executable, CLI_PATH] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT}
    )
    assert result.returncode == 0
    assert expect in result.stdout


def test_cli_invalid_command_fails():
    result = subprocess.run(
        [sys.executable, CLI_PATH, "prompt", "--type", "invalid", "--input", "test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT}
    )
    # Even if it returns 0, it should produce an error message
    assert "Unknown prompt type" in result.stderr or "Error" in result.stdout or "Error" in result.stderr


# Test the DSL subcommand outputs correct JSON
def test_dsl_subcommand_outputs_json():
    dsl_input = "[persona: Research Assistant][task: Summarize][length: 3 bullet points]"
    result = subprocess.run(
        [sys.executable, CLI_PATH, "dsl", "--input", dsl_input],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT}
    )
    assert result.returncode == 0
    stdout = result.stdout.strip()
    # Should parse as JSON and contain keys
    ctx = json.loads(stdout)
    assert ctx["persona"] == "Research Assistant"
    assert ctx["task"] == "Summarize"
    assert ctx["length"] == "3 bullet points"


def test_dsl_subcommand_can_show_the_interpretation_stages():
    dsl_input = "[persona: Research Assistant][task: Summarize][length: 3 bullet points]"
    result = subprocess.run(
        [
            sys.executable,
            CLI_PATH,
            "dsl",
            "--input",
            dsl_input,
            "--show-stages",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["tokens"] == [
        "LBRACK", "IDENT", "COLON", "VALUE", "RBRACK",
        "LBRACK", "IDENT", "COLON", "VALUE", "RBRACK",
        "LBRACK", "IDENT", "COLON", "VALUE", "RBRACK", "EOF",
    ]
    assert output["expressions"] == ["PersonaExpr", "TaskExpr", "LengthExpr"]
    assert output["context"]["length"] == "3 bullet points"
    assert "Persona: Research Assistant" in output["prompt"]


def test_dsl_subcommand_rejects_invalid_semantics():
    result = subprocess.run(
        [
            sys.executable,
            CLI_PATH,
            "dsl",
            "--input",
            "[task: translate][length: 3 bullet points]",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
    )

    assert result.returncode == 2
    assert "ValidationError" in result.stderr


def test_dsl_subcommand_rejects_malformed_input():
    result = subprocess.run(
        [sys.executable, CLI_PATH, "dsl", "--input", "[task summarize]"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
    )

    assert result.returncode == 2
    assert "ParseError" in result.stderr


# Test --dsl flag merges into prompt context
def test_prompt_with_dsl_merges_into_context():
    dsl_input = "[persona: Research Assistant][tone: optimistic][task: summarize][length: 3 bullet points][format: bullets]"
    result = subprocess.run(
        [
            sys.executable, CLI_PATH, "prompt",
            "--type", "summarize",
            "--input", "Summarize this message",
            "--context", "Extra context",
            "--dsl", dsl_input
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT}
    )
    assert result.returncode == 0
    output = result.stdout
    # Expect merged persona and tone
    assert "Research Assistant" in output
    assert "optimistic" in output
    # Expect length and format present in context
    assert "3 bullet points" in output
    assert "bullets" in output
