

from typing import Dict, TypedDict
from .lexer import lex
from .parser import Parser
from .errors import ValidationError
from .validators import validate_context

class PromptContext(TypedDict, total=False):
    persona: str
    task: str
    length: str
    format: str
    tone: str
    source: str

def evaluate(expressions, context: Dict[str, str]) -> Dict[str, str]:
    for expr in expressions:
        expr.interpret(context)
    return context

def interpret_prompt_dsl(text: str) -> PromptContext:
    tokens = lex(text or "")
    exprs = Parser(tokens).parse()
    ctx: Dict[str, str] = {}
    evaluate(exprs, ctx)
    validate_context(ctx)
    return ctx  # type: ignore[return-value]