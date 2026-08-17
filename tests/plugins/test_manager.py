import pytest

from metis.plugins import (
    PluginActivationError,
    PluginManager,
    PluginMetadata,
)

from .conftest import FakeEntryPoint


class CommandPlugin:
    metadata = PluginMetadata("demo", "1.0.0")

    def __init__(self) -> None:
        self.register_calls = 0

    def register(self, registrar) -> None:
        self.register_calls += 1
        registrar.command("demo.echo", lambda: object())


class IncompatiblePlugin(CommandPlugin):
    metadata = PluginMetadata("demo", "1.0.0", api_version="99")


def test_disabled_candidate_is_never_loaded(registries) -> None:
    entry_point = FakeEntryPoint("demo", CommandPlugin())

    report = PluginManager(registries).activate({}, candidates=[entry_point])

    assert report.disabled[0].plugin_id == "demo"
    assert entry_point.load_calls == 0


def test_activation_is_idempotent(registries) -> None:
    plugin = CommandPlugin()
    entry_point = FakeEntryPoint("demo", plugin)
    manager = PluginManager(registries)
    config = {"enabled_plugins": ["demo"]}

    first = manager.activate(config, candidates=[entry_point])
    second = manager.activate(config, candidates=[entry_point])

    assert first is second
    assert first.loaded[0].plugin_version == "1.0.0"
    assert entry_point.load_calls == plugin.register_calls == 1


def test_incompatible_api_fails_before_register(registries) -> None:
    plugin = IncompatiblePlugin()
    entry_point = FakeEntryPoint("demo", plugin)

    report = PluginManager(registries).activate(
        {"enabled_plugins": ["demo"]},
        candidates=[entry_point],
    )

    assert report.rejected[0].error_category == "contract"
    assert plugin.register_calls == 0
    assert "demo.echo" not in registries.commands


def test_duplicate_entry_point_names_are_rejected_without_loading(registries) -> None:
    first = FakeEntryPoint("demo", CommandPlugin(), distribution="first")
    second = FakeEntryPoint("demo", CommandPlugin(), distribution="second")

    report = PluginManager(registries).activate(
        {"enabled_plugins": ["demo"]},
        candidates=[second, first],
    )

    assert len(report.rejected) == 2
    assert all(
        record.error_category == "duplicate-entry-point" for record in report.rejected
    )
    assert first.load_calls == second.load_calls == 0


def test_strict_mode_raises_with_report_for_missing_plugin(registries) -> None:
    with pytest.raises(PluginActivationError) as caught:
        PluginManager(registries).activate(
            {"enabled_plugins": ["missing"], "strict_plugins": True},
            candidates=[],
        )

    assert caught.value.report.rejected[0].error_category == "not-installed"


def test_permissive_mode_returns_visible_load_error(registries) -> None:
    entry_point = FakeEntryPoint("demo", RuntimeError("broken import"))

    report = PluginManager(registries).activate(
        {"enabled_plugins": ["demo"]},
        candidates=[entry_point],
    )

    assert report.rejected[0].error_category == "load-error"
    assert "broken import" in report.rejected[0].message
