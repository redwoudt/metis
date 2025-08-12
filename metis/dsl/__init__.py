

"""
Metis Prompt DSL package.

Public API:
  - interpret_prompt_dsl(text: str) -> PromptContext
  - PromptContext: dict-like context produced by interpretation
  - Errors: LexError, ParseError, ValidationError, UnknownKeyError
"""
from .interpreter import interpret_prompt_dsl, PromptContext
from .errors import LexError, ParseError, ValidationError, UnknownKeyError
from .grammar import EBNF, KNOWN_KEYS

__all__ = [
    "interpret_prompt_dsl",
    "PromptContext",
    "LexError",
    "ParseError",
    "ValidationError",
    "UnknownKeyError",
    "EBNF",
    "KNOWN_KEYS",
]