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