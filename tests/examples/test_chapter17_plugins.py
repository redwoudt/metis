import sys
from dataclasses import dataclass

from metis.commands.base import ToolCommand, ToolContext
from metis.examples.chapter17_plugins import main
from metis.plugins import PluginMetadata


class EchoCommand(ToolCommand):
    name = "echo.echo"

    def execute(self, context: ToolContext):
        return {"echo": context.args.get("message", "")}


class EchoPlugin:
    metadata = PluginMetadata("echo", "1.0.0")

    def register(self, registrar) -> None:
        registrar.command("echo.echo", EchoCommand)


@dataclass(frozen=True)
class FakeDistribution:
    name: str = "metis-echo-plugin"
    version: str = "1.0.0"


class FakeEntryPoint:
    name = "echo"
    value = "metis_echo_plugin:EchoPlugin"
    group = "metis_genai.plugins"
    dist = FakeDistribution()

    @staticmethod
    def load():
        return EchoPlugin


def test_chapter17_example_loads_and_lists_an_enabled_plugin(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        "metis.plugins.manager.discover_plugins",
        lambda: (FakeEntryPoint(),),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["chapter17_plugins", "--enable", "echo", "--list"],
    )

    assert main() == 0

    assert capsys.readouterr().out.splitlines() == [
        "LOADED   echo@1.0.0",
        "COMMAND  echo.echo owner=echo",
    ]

