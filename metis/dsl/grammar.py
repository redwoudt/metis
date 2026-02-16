"""
Grammar and canonical keys for the Metis Prompt DSL.

The DSL is a sequence of bracketed key-value pairs:

    [key: value][key: value]...

This grammar is intentionally minimal to keep the Interpreter
Pattern focused and easy to reason about.
"""

from typing import Final, Set

EBNF: Final[str] = """
prompt      ::= expression*
expression  ::= "[" key ":" value "]"
key         ::= IDENT
value       ::= VALUE
"""

# Canonical keys supported by the DSL.
# These are interpreted into a structured context dictionary.
KNOWN_KEYS: Set[str] = {
    # Prompt shaping
    "persona",
    "task",
    "length",
    "format",
    "tone",
    "source",

    # Tool execution (Chapter 8)
    "tool",
    "args",
    "tool_call",
}