from typing import List
from .tokens import Token, TokenType
from .errors import ParseError, UnknownKeyError
from .ast import (
    Expression,
    PersonaExpr,
    TaskExpr,
    LengthExpr,
    FormatExpr,
    ToneExpr,
    SourceExpr,
    ToolExpr,
    ArgsExpr,
    ToolCallExpr,
)


KEY_TO_EXPR = {
    "persona": PersonaExpr,
    "task": TaskExpr,
    "length": LengthExpr,
    "format": FormatExpr,
    "tone": ToneExpr,
    "source": SourceExpr,

    # Tool execution (Chapter 8)
    "tool": ToolExpr,
    "args": ArgsExpr,
    "tool_call": ToolCallExpr,
}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[Expression]:
        exprs: List[Expression] = []
        while not self._is_at_end():
            if self._check(TokenType.LBRACK):
                exprs.append(self._expression())
            else:
                self._advance()
        return exprs

    def _expression(self) -> Expression:
        self._consume(TokenType.LBRACK, "Expected '[' to start DSL expression.")
        key_tok = self._consume(TokenType.IDENT, "Expected IDENT inside DSL expression.")
        self._consume(TokenType.COLON, "Expected ':' after DSL key.")
        val_tok = self._consume(TokenType.VALUE, "Expected VALUE after ':' in DSL expression.")
        self._consume(TokenType.RBRACK, "Expected ']' to end DSL expression.")

        key = (key_tok.lexeme or "").strip().lower()
        raw_value = (val_tok.lexeme or "").strip()

        expr_cls = KEY_TO_EXPR.get(key)
        if not expr_cls:
            raise UnknownKeyError(key)

        # ArgsExpr / ToolCallExpr want raw string, others want a value string
        if expr_cls in (ArgsExpr, ToolCallExpr):
            return expr_cls(raw_value)  # type: ignore[misc]
        return expr_cls(raw_value)  # type: ignore[misc]

    def _consume(self, ttype: str, message: str) -> Token:
        if self._check(ttype):
            return self._advance()
        tok = self._peek()
        raise ParseError(message, tok.line, tok.col)

    def _check(self, ttype: str) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == ttype

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]