

"""
Metis Prompt DSL package.

Public API:
  - interpret_prompt_dsl(text: str) -> PromptContext
  - split_prompt_dsl(text: str) -> tuple[PromptContext, str]
  - PromptContext: dict-like context produced by interpretation
  - Errors: LexError, ParseError, ValidationError, UnknownKeyError
"""
from .interpreter import interpret_prompt_dsl, split_prompt_dsl, PromptContext
from .errors import DslError, LexError, ParseError, ValidationError, UnknownKeyError
from .grammar import EBNF, KNOWN_KEYS

__all__ = [
    "interpret_prompt_dsl",
    "split_prompt_dsl",
    "PromptContext",
    "DslError",
    "LexError",
    "ParseError",
    "ValidationError",
    "UnknownKeyError",
    "EBNF",
    "KNOWN_KEYS",
]
