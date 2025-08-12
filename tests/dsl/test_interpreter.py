import pytest

from metis.dsl import (
    interpret_prompt_dsl,
    LexError,
    ParseError,
    ValidationError,
    UnknownKeyError,
)
from metis.dsl.lexer import lex
from metis.dsl.parser import Parser
from metis.dsl.interpreter import evaluate
from metis.dsl.ast import PersonaExpr, TaskExpr, LengthExpr


def test_lex_simple_blocks():
    text = "[persona: Research Assistant][task: Summarize][length: 3 bullet points]"
    tokens = lex(text)
    # Should end with EOF and include brackets/idents/values along the way
    assert tokens[-1].type.name == "EOF"
    # Quick sanity: at least one LBRACK and one RBRACK
    assert any(t.type.name == "LBRACK" for t in tokens)
    assert any(t.type.name == "RBRACK" for t in tokens)


def test_parse_to_expressions():
    text = "[persona: Analyst][task: Summarize][length: 5 bullets]"
    tokens = lex(text)
    exprs = Parser(tokens).parse()
    # Should produce three expression objects of the expected classes
    assert len(exprs) == 3
    assert any(isinstance(e, PersonaExpr) for e in exprs)
    assert any(isinstance(e, TaskExpr) for e in exprs)
    assert any(isinstance(e, LengthExpr) for e in exprs)


def test_interpret_builds_context():
    text = "[persona: Research Assistant][task: Summarize][length: 3 bullet points][format: bullets][tone: optimistic]"
    ctx = interpret_prompt_dsl(text)
    assert ctx["persona"] == "Research Assistant"
    assert ctx["task"].lower() == "summarize"
    assert ctx["length"] == "3 bullet points"
    assert ctx["format"] == "bullets"
    assert ctx["tone"] == "optimistic"


def test_empty_input_yields_empty_context():
    ctx = interpret_prompt_dsl("")
    assert ctx == {}


def test_whitespace_and_case_insensitive_keys():
    # Keys should be case-insensitive; stray whitespace should be tolerated
    text = " [PeRsOnA :  Analyst ]  [ TASK:   summarize ] "
    ctx = interpret_prompt_dsl(text)
    assert ctx["persona"] == "Analyst"
    assert ctx["task"] == "summarize"


def test_validation_length_requires_summarize():
    # length without summarize task should raise ValidationError
    bad = "[length: 5 bullets][task: translate]"
    with pytest.raises(ValidationError):
        interpret_prompt_dsl(bad)

    # With summarize it should pass
    good = "[task: summarize][length: 5 bullets]"
    ctx = interpret_prompt_dsl(good)
    assert ctx["length"] == "5 bullets"
    assert ctx["task"] == "summarize"


def test_validation_source_must_be_url():
    bad = "[task: summarize][source: not-a-url]"
    with pytest.raises(ValidationError):
        interpret_prompt_dsl(bad)

    ok = "[task: summarize][source: https://example.com/doc]"
    ctx = interpret_prompt_dsl(ok)
    assert ctx["source"].startswith("https://")


def test_unknown_key_raises():
    # 'audience' isn't in the core grammar mapping; should raise UnknownKeyError
    text = "[audience: kids]"
    with pytest.raises(UnknownKeyError):
        interpret_prompt_dsl(text)


def test_parse_errors_for_malformed_blocks():
    # Missing closing bracket
    text = "[persona: Analyst"
    with pytest.raises(ParseError):
        interpret_prompt_dsl(text)

    # Missing colon
    text2 = "[persona Analyst]"
    with pytest.raises(ParseError):
        interpret_prompt_dsl(text2)


def test_manual_evaluate_walks_expressions():
    # Show the evaluate() step explicitly for the chapter narrative
    tokens = lex("[persona: Analyst][task: Summarize]")
    exprs = Parser(tokens).parse()
    ctx = {}
    out = evaluate(exprs, ctx)
    assert out is ctx  # evaluate mutates and returns the same dict
    assert ctx["persona"] == "Analyst"
    assert ctx["task"] == "Summarize"