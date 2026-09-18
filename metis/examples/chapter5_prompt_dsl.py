"""Trace the Chapter 5 prompt DSL from source text to a rendered prompt."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from metis.dsl import DslError, interpret_prompt_dsl
from metis.dsl.lexer import lex
from metis.dsl.parser import Parser
from metis.prompts.builders.default_prompt_builder import DefaultPromptBuilder


DEFAULT_DSL = (
    "[persona: Research Assistant]"
    "[task: Summarize]"
    "[length: 3 bullet points]"
)


def run_demo(dsl_text: str = DEFAULT_DSL) -> dict[str, Any]:
    """Return the observable stages of the canonical Prompt DSL pipeline."""
    tokens = lex(dsl_text)
    expressions = Parser(tokens).parse()
    context = dict(interpret_prompt_dsl(dsl_text))
    prompt = DefaultPromptBuilder().build_with_context(context).render()

    return {
        "source": dsl_text,
        "tokens": [token.type.name for token in tokens],
        "expressions": [type(expression).__name__ for expression in expressions],
        "context": context,
        "prompt": prompt,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=DEFAULT_DSL,
        help="Bracket DSL such as '[task: Summarize][length: 3 bullets]'",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_demo(args.input)
    except DslError as exc:
        print(f"ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
