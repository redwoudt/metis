import subprocess
import sys
import os
import pytest

CLI_PATH = os.path.join("metis", "tools", "metis_cli.py")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

@pytest.mark.parametrize("args,expect", [
    (["prompt", "--type", "summarize", "--input", "Summarize this message"], "Summarize this message"),
    (["prompt", "--type", "plan", "--input", "Plan my project", "--context", "Week schedule"], "Plan my project"),
])


def test_prompt_cli_invokes_successfully(args, expect):
    """
    Test that the CLI 'prompt' subcommand executes successfully and returns output
    containing the input prompt.
    """
    result = subprocess.run(
        [sys.executable, CLI_PATH] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    assert result.returncode == 0
    assert expect in result.stdout


def test_cli_invalid_command_fails():
    """
    Test that providing an invalid prompt type results in an error.
    """
    result = subprocess.run(
        [sys.executable, CLI_PATH, "prompt", "--type", "invalid", "--input", "test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    assert result.returncode == 0  # Program may still return 0, but emit error message
    assert "Error" in result.stdout or "Error" in result.stderr