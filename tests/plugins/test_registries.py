import pytest

from metis.behavior import BehaviorPlan
from metis.plugins import (
    PluginContractError,
    PluginMetadata,
    RegistryFrozenError,
)


class EchoCommand:
    pass


def test_failed_batch_commits_nothing(registries) -> None:
    metadata = PluginMetadata("atomic", "1.0.0")

    with pytest.raises(PluginContractError, match="unknown model role"):
        with registries.stage(metadata) as registrar:
            registrar.command("atomic.echo", EchoCommand)
            registrar.behavior_template(
                BehaviorPlan(
                    name="atomic.invalid",
                    model_role="not-a-role",
                    response_style="default",
                    allow_tools=True,
                    require_safety=True,
                )
            )

    assert "atomic.echo" not in registries.commands
    assert "atomic.invalid" not in registries.behavior_templates


def test_external_names_must_use_plugin_namespace(registries) -> None:
    with pytest.raises(PluginContractError, match="atomic.*namespace"):
        with registries.stage(PluginMetadata("atomic", "1.0.0")) as registrar:
            registrar.command("echo", EchoCommand)


def test_successful_batch_records_provenance(registries) -> None:
    with registries.stage(PluginMetadata("atomic", "1.0.0")) as registrar:
        registrar.command("atomic.echo", EchoCommand)

    assert registries.commands["atomic.echo"] is EchoCommand
    assert registries.owner_of("command", "atomic.echo") == "atomic"


def test_empty_plugin_is_rejected(registries) -> None:
    with pytest.raises(PluginContractError, match="registered no contributions"):
        with registries.stage(PluginMetadata("empty", "1.0.0")):
            pass


def test_registries_reject_mutation_after_freeze(registries) -> None:
    registries.freeze()

    with pytest.raises(RegistryFrozenError):
        with registries.stage(PluginMetadata("late", "1.0.0")):
            pass
