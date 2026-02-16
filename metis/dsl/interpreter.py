from typing import Dict, TypedDict, Any
from .lexer import lex
from .parser import Parser
from .errors import ValidationError
from .validators import validate_context


class PromptContext(TypedDict, total=False):
    # Prompt shaping
    persona: str
    task: str
    length: str
    format: str
    tone: str
    source: str

    # Tool execution (Chapter 8)
    tool: str
    args: Dict[str, Any]
    tool_call: Dict[str, Any]


def evaluate(expressions, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Walk the parsed DSL expressions and let each expression
    mutate the shared context.
    """
    for expr in expressions:
        expr.interpret(context)
    return context


def interpret_prompt_dsl(text: str) -> PromptContext:
    """
    Entry point for DSL interpretation.

    Converts DSL text like:

        [tool: search_web][args: {"query": "malbec"}]

    into a structured context dictionary.
    """
    tokens = lex(text or "")
    exprs = Parser(tokens).parse()

    ctx: Dict[str, Any] = {}
    evaluate(exprs, ctx)

    # Validate known prompt-related keys.
    # Tool keys are allowed and validated separately downstream.
    try:
        validate_context(
            {
                k: v
                for k, v in ctx.items()
                if k
                in {
                    "persona",
                    "task",
                    "length",
                    "format",
                    "tone",
                    "source",
                }
            }
        )
    except ValidationError:
        raise

    return ctx  # type: ignore[return-value]