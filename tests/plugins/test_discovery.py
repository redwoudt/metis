from metis.plugins.discovery import discover_plugins

from .conftest import FakeEntryPoint


def test_discovery_filters_group_sorts_and_does_not_load() -> None:
    beta = FakeEntryPoint("beta", object())
    ignored = FakeEntryPoint("ignored", object(), group="another.group")
    alpha = FakeEntryPoint("alpha", object())

    candidates = discover_plugins(entry_points_provider=lambda: [beta, ignored, alpha])

    assert [candidate.name for candidate in candidates] == ["alpha", "beta"]
    assert alpha.load_calls == beta.load_calls == ignored.load_calls == 0
