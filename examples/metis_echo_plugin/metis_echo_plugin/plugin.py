"""A harmless command contribution delivered outside the Mêtis package."""

from typing import Any

from metis.commands.base import ToolCommand, ToolContext
from metis.plugins import PluginMetadata, PluginRegistrar


class EchoCommand(ToolCommand):
    name = "echo.repeat"

    def execute(self, context: ToolContext) -> dict[str, Any]:
        return {"echo": context.args.get("message", "")}


class EchoPlugin:
    metadata = PluginMetadata("echo", "1.0.0")

    def register(self, registrar: PluginRegistrar) -> None:
        registrar.command("echo.repeat", EchoCommand)


plugin = EchoPlugin()
