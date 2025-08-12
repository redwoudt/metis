import pytest
from metis.dsl.lexer import lex
from metis.dsl.tokens import TokenType
from metis.dsl.errors import LexError


def test_lex_single_expression():
    text = "[persona: Analyst]"
    tokens = lex(text)
    # Expected sequence: LBRACK IDENT COLON VALUE RBRACK EOF
    types = [t.type for t in tokens]
    assert types[0] == TokenType.LBRACK
    assert types[1] == TokenType.IDENT
    assert types[2] == TokenType.COLON
    assert types[3] == TokenType.VALUE
    assert types[4] == TokenType.RBRACK
    assert types[-1] == TokenType.EOF


def test_lex_multiple_expressions():
    text = "[persona: Analyst][task: Summarize]"
    tokens = lex(text)
    # Two LBRACK and two RBRACK expected
    assert sum(1 for t in tokens if t.type == TokenType.LBRACK) == 2
    assert sum(1 for t in tokens if t.type == TokenType.RBRACK) == 2


def test_whitespace_and_case_tolerance():
    text = " [PERSONA : Analyst ] "
    tokens = lex(text)
    # First IDENT should be 'PERSONA'
    ident_token = next(t for t in tokens if t.type == TokenType.IDENT)
    assert ident_token.lexeme.lower() == "persona"


def test_value_with_spaces():
    text = "[task: Summarize in detail]"
    tokens = lex(text)
    value_token = next(t for t in tokens if t.type == TokenType.VALUE)
    assert value_token.lexeme == "Summarize in detail"


def test_empty_value_allowed():
    text = "[task: ]"
    tokens = lex(text)
    # Should still produce a VALUE token, possibly empty
    value_token = next(t for t in tokens if t.type == TokenType.VALUE)
    assert value_token.lexeme == ""


def test_unexpected_character_raises():
    bad_text = "[persona: Analyst]$"
    with pytest.raises(LexError):
        lex(bad_text)


def test_eof_always_present():
    text = "[persona: Analyst]"
    tokens = lex(text)
    assert tokens[-1].type == TokenType.EOF