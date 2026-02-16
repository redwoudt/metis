import pytest
from metis.commands.generate import GenerateImageCommand
from metis.commands.base import ToolContext


def test_generate_image_executes():
    cmd = GenerateImageCommand()
    ctx = ToolContext(
        command=cmd,
        args={"prompt": "Vineyard at sunset"},
        user="u1"
    )
    out = cmd.execute(ctx)

    assert isinstance(out, dict)
    assert "image_url" in out
    assert out["image_url"].startswith("http")


def test_generate_image_missing_prompt():
    cmd = GenerateImageCommand()
    ctx = ToolContext(command=cmd, args={}, user="u1")
    with pytest.raises(ValueError):
        cmd.execute(ctx)