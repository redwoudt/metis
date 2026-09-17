from dataclasses import dataclass
from typing import Any, Dict

from metis.dsl import KNOWN_KEYS, interpret_prompt_dsl
from metis.dsl.ast import Expression
from metis.dsl.registry import register_key


@dataclass
class AudienceExprForTest(Expression):
    value: str

    def interpret(self, context: Dict[str, Any]) -> None:
        context["test_audience"] = self.value


def test_registered_key_changes_parser_behavior():
    register_key("test_audience", AudienceExprForTest)

    ctx = interpret_prompt_dsl("[test_audience: researchers]")

    assert ctx["test_audience"] == "researchers"
    assert "test_audience" in KNOWN_KEYS
