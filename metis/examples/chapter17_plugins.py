"""List installed Mêtis plugins and optionally activate named candidates."""

from __future__ import annotations

import argparse

from metis.plugins import ExtensionRegistries, PluginManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--enable",
        action="append",
        default=[],
        metavar="PLUGIN",
        help="Enable one installed plugin; repeat to enable several",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when an enabled plugin cannot be activated",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the final plugin and command state",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registries = ExtensionRegistries.with_builtins()
    report = PluginManager(registries).activate(
        {
            "enabled_plugins": args.enable,
            "strict_plugins": args.strict,
        }
    )
    registries.freeze()

    if args.list or not args.enable:
        for record in report.records:
            version = f"@{record.plugin_version}" if record.plugin_version else ""
            detail = f" ({record.message})" if record.message else ""
            print(f"{record.status.upper():8} {record.plugin_id}{version}{detail}")

        contributed = sorted(
            name
            for name in registries.commands
            if registries.owner_of("command", name) != "metis"
        )
        for command_name in contributed:
            owner = registries.owner_of("command", command_name)
            print(f"COMMAND  {command_name} owner={owner}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
