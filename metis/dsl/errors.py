class DslError(Exception):
    """Base class for all DSL-related errors."""

class LexError(DslError):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"LexError at {line}:{col} - {message}")
        self.line = line
        self.col = col

class ParseError(DslError):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"ParseError at {line}:{col} - {message}")
        self.line = line
        self.col = col

class ValidationError(DslError):
    """Raised when the interpreted context violates semantic rules."""

class UnknownKeyError(DslError):
    def __init__(self, key: str):
        super().__init__(f"Unknown DSL key: {key!r}")
        self.key = key
