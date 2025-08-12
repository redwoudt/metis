import pytest
from metis.dsl.lexer import lex
from metis.dsl.parser import Parser
from metis.dsl.errors import ParseError, UnknownKeyError
from metis.dsl.ast import PersonaExpr, TaskExpr, LengthExpr


def parse_text(text: str):
    """Helper: lex and parse in one call."""
    tokens = lex(text)
    return Parser(tokens).parse()


def test_parse_single_expression():
    exprs = parse_text("[persona: Analyst]")
    assert len(exprs) == 1
    assert isinstance(exprs[0], PersonaExpr)


def test_parse_multiple_expressions():
    exprs = parse_text("[persona: Analyst][task: Summarize][length: 3 bullet points]")
    types = {type(e) for e in exprs}
    assert PersonaExpr in types
    assert TaskExpr in types
    assert LengthExpr in types
    assert len(exprs) == 3


def test_parser_trims_whitespace_and_is_case_insensitive():
    exprs = parse_text("[  PERSONA  :  Analyst  ] [TASK: summarize]")
    assert isinstance(exprs[0], PersonaExpr)
    assert isinstance(exprs[1], TaskExpr)


def test_parser_allows_empty_value():
    exprs = parse_text("[task: ]")
    assert isinstance(exprs[0], TaskExpr)


def test_parser_raises_for_missing_brackets():
    with pytest.raises(ParseError):
        parse_text("[persona: Analyst")  # missing closing bracket


def test_parser_raises_for_missing_colon():
    with pytest.raises(ParseError):
        parse_text("[persona Analyst]")  # missing colon


def test_parser_raises_for_unknown_key():
    with pytest.raises(UnknownKeyError):
        parse_text("[audience: Kids]")  # not in KNOWN_KEYS


def test_order_preserved_in_expressions():
    exprs = parse_text("[persona: Analyst][task: Summarize]")
    # The parser should preserve the input order
    assert isinstance(exprs[0], PersonaExpr)
    assert isinstance(exprs[1], TaskExpr)