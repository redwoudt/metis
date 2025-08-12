"""
Grammar and canonical keys for the Metis Prompt DSL.
The DSL is a sequence of bracketed key-value pairs:

    [key: value][key: value]...

Minimal EBNF (kept simple by design):

    prompt      ::= expression*
    expression  ::= "[" key ":" value "]"
    key         ::= IDENT                   ; canonical: persona|task|length|format|tone|source
    value       ::= VALUE                   ; any run of characters without ']' (trimmed)

Notes:
- No nesting/conditionals (keep Interpreter example focused).
- Keys are case-insensitive, canonicalized to lowercase.
- Whitespace around separators is ignored.
"""
from typing import Final, Set

EBNF: Final[str] = """
prompt      ::= expression*
expression  ::= "[" key ":" value "]"
key         ::= IDENT
value       ::= VALUE
"""

# Canonical keys supported by core. Extensions may add via registry.
KNOWN_KEYS: Set[str] = {"persona", "task", "length", "format", "tone", "source"}
