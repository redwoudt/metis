import pytest

from metis.dsl.lexer import Lexer
from metis.dsl.parser import Parser


def _interpret(dsl_text: str) -> dict:
    """
    Parse DSL and interpret expressions into a context dict.

    This mirrors how RequestHandler builds dsl_ctx.
    """
    tokens = Lexer(dsl_text).tokenize()
    ast = Parser(tokens).parse()

    ctx: dict = {}
    for expr in ast:
        expr.interpret(ctx)
    return ctx


def test_dsl_style_expr_sets_style_in_context():
    ctx = _interpret("[style: detailed] Hello")
    assert ctx["style"] == "detailed"


@pytest.mark.parametrize(
    "dsl_value, expected",
    [
        ("true", True), ("false", False),
        ("yes", True), ("no", False),
        ("on", True), ("off", False),
        ("1", True), ("0", False),
        ("TRUE", True), ("False", False),
        ("bogus", False), ("", False),
    ],
)
def test_dsl_boolean_flags_parse_common_values(dsl_value, expected):
    ctx = _interpret(
        f"[safety_enabled: {dsl_value}]"
        f"[format_markdown: {dsl_value}]"
        f"[include_citations: {dsl_value}] Hello"
    )
    assert ctx["safety_enabled"] is expected
    assert ctx["format_markdown"] is expected
    assert ctx["include_citations"] is expected