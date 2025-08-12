

from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    LBRACK = auto()
    RBRACK = auto()
    COLON = auto()
    IDENT = auto()
    VALUE = auto()
    EOF = auto()

@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.lexeme!r}, {self.line}:{self.col})"