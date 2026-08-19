"""Run a governed weather command without contacting an external provider."""

from __future__ import annotations

import argparse
import logging
from types import SimpleNamespace
from typing import Any

from metis.commands import command_registry
from metis.commands.base import ToolCommand, ToolContext
from metis.tools import ToolExecutor


class WeatherCommand(ToolCommand):
    """Return a deterministic forecast through the strict execution pipeline."""

    name = "weather"
    execution_policy = "strict"

    def execute(self, context: ToolContext) -> dict[str, str]:
        city = context.args.get("city")
        if not city:
            raise ValueError("Missing city.")
        return {"city": city, "forecast": "clear"}


class DemoQuota:
    """Record quota checks and optionally deny the weather request."""

    def __init__(self, *, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[tuple[Any, str]] = []

    def allow(self, user_id: Any, tool_name: str) -> bool:
        self.calls.append((user_id, tool_name))
        return self.allowed


def build_executor(*, allow: bool = True) -> ToolExecutor:
    """Compose the example command with the application's normal invoker."""
    services = SimpleNamespace(
        quota=DemoQuota(allowed=allow),
        audit_logger=logging.getLogger("metis.chapter8.weather"),
    )
    commands = dict(command_registry)
    commands[WeatherCommand.name] = WeatherCommand
    return ToolExecutor(services=services, commands=commands)


def run_weather(city: str, *, allow: bool = True) -> dict[str, str]:
    """Execute one weather request through lookup and the handler chain."""
    return build_executor(allow=allow).execute_tool(
        WeatherCommand.name,
        args={"city": city},
        user="reader-01",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default="Ithaca")
    parser.add_argument(
        "--deny",
        action="store_true",
        help="Deny the request at the quota boundary before execution",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = run_weather(args.city, allow=not args.deny)
    except RuntimeError as exc:
        print(f"blocked={exc}")
        return 2

    print(f"city={result['city']}")
    print(f"forecast={result['forecast']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
