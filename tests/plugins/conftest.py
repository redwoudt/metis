from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from metis.plugins import ExtensionRegistries


@dataclass(frozen=True)
class FakeDistribution:
    name: str = "metis-test-plugin"
    version: str = "1.0.0"


class FakeEntryPoint:
    def __init__(
        self,
        name: str,
        plugin: Any,
        *,
        distribution: str = "metis-test-plugin",
        version: str = "1.0.0",
        group: str = "metis_genai.plugins",
    ) -> None:
        self.name = name
        self.value = f"tests.plugins:{name}"
        self.group = group
        self.dist = FakeDistribution(distribution, version)
        self._plugin = plugin
        self.load_calls = 0

    def load(self) -> Any:
        self.load_calls += 1
        if isinstance(self._plugin, Exception):
            raise self._plugin
        return self._plugin


@pytest.fixture
def registries() -> ExtensionRegistries:
    return ExtensionRegistries.with_builtins()
