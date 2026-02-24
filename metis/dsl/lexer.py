import re
from typing import List
from .tokens import Token, TokenType
from .errors import LexError

_WS = re.compile(r"\s+")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_\-]*")

def lex(text: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    after_colon = False  # when True, consume VALUE up to next ']'

    def advance(n: int = 1):
        nonlocal i, line, col
        for _ in range(n):
            if i < len(text) and text[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1

    while i < len(text):
        # Whitespace is always skipped but does not reset after_colon
        m = _WS.match(text, i)
        if m:
            advance(m.end() - i)
            continue

        if after_colon:
            # Capture everything up to the next ']' (could be empty)
            start_line, start_col = line, col
            j = i
            while j < len(text) and text[j] != "]":
                j += 1
            raw = text[i:j]
            value = raw.strip()
            tokens.append(Token(TokenType.VALUE, value, start_line, start_col))
            advance(j - i)
            after_colon = False
            # Leave the ']' for the next loop to emit RBRACK
            continue

        ch = text[i]

        if ch == "[":
            tokens.append(Token(TokenType.LBRACK, "[", line, col))
            advance()
            continue
        if ch == "]":
            tokens.append(Token(TokenType.RBRACK, "]", line, col))
            advance()
            continue
        if ch == ":":
            tokens.append(Token(TokenType.COLON, ":", line, col))
            advance()
            after_colon = True
            continue

        m_ident = _IDENT.match(text, i)
        if m_ident:
            lexeme = m_ident.group(0)
            tokens.append(Token(TokenType.IDENT, lexeme, line, col))
            advance(len(lexeme))
            continue

        # Any other visible character outside of VALUE/whitespace is invalid
        raise LexError(f"Unexpected character {ch!r}", line, col)

    tokens.append(Token(TokenType.EOF, "", line, col))
    return tokens


class Lexer:
    """Backwards-compatible wrapper for the DSL lexer.

    Older code (and tests) expects a `Lexer` class that can be instantiated and then
    asked for tokens. The implementation in this module is function-based (`lex`).
    This wrapper preserves the original import surface: `from metis.dsl.lexer import Lexer`.
    """

    def __init__(self, text: str):
        self.text = text

    def lex(self) -> List[Token]:
        """Lex the configured input text into a list of tokens."""
        return lex(self.text)

    def tokenize(self) -> List[Token]:
        """Alias for `lex()` for compatibility with callers that expect `tokenize()`."""
        return self.lex()