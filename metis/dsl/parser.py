

from typing import List
from .tokens import Token, TokenType
from .errors import ParseError, UnknownKeyError
from .ast import (
    Expression, PersonaExpr, TaskExpr, LengthExpr, FormatExpr, ToneExpr, SourceExpr
)
from .grammar import KNOWN_KEYS

KEY_TO_EXPR = {
    "persona": PersonaExpr,
    "task": TaskExpr,
    "length": LengthExpr,
    "format": FormatExpr,
    "tone": ToneExpr,
    "source": SourceExpr,
}

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def _peek(self) -> Token:
        return self.tokens[self.i]

    def _consume(self, ttype: TokenType, message: str) -> Token:
        tok = self._peek()
        if tok.type != ttype:
            raise ParseError(message + f" (found {tok.type.name})", tok.line, tok.col)
        self.i += 1
        return tok

    def parse(self) -> List[Expression]:
        exprs: List[Expression] = []
        while self._peek().type != TokenType.EOF:
            exprs.append(self._expression())
        return exprs

    def _expression(self) -> Expression:
        self._consume(TokenType.LBRACK, "Expected '[' to start expression")
        key_tok = self._peek()
        if key_tok.type not in (TokenType.IDENT, TokenType.VALUE):
            raise ParseError("Expected key identifier", key_tok.line, key_tok.col)
        self.i += 1
        self._consume(TokenType.COLON, "Expected ':' after key")
        val_tok = self._peek()
        if val_tok.type not in (TokenType.IDENT, TokenType.VALUE):
            raise ParseError("Expected value after ':'", val_tok.line, val_tok.col)
        self.i += 1
        self._consume(TokenType.RBRACK, "Expected ']' at end of expression")

        key = key_tok.lexeme.strip().lower()
        value = val_tok.lexeme.strip()
        if key not in KNOWN_KEYS and key not in KEY_TO_EXPR:
            raise UnknownKeyError(key)
        ctor = KEY_TO_EXPR.get(key)
        if ctor is None:
            raise UnknownKeyError(key)
        return ctor(value)