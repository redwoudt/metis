"""
Grammar and canonical keys for the Metis Prompt DSL.

The DSL is a sequence of bracketed key-value pairs:

    [key: value][key: value]...

This grammar is intentionally minimal to keep the Interpreter
Pattern focused and easy to reason about.
"""

from typing import Final

from .registry import KNOWN_KEYS

EBNF: Final[str] = """
prompt      ::= expression*
expression  ::= "[" key ":" value "]"
key         ::= IDENT
value       ::= VALUE
"""

# KNOWN_KEYS is imported from registry.py so the grammar, parser, and
# extension mechanism share one live source of truth.
