

from typing import Dict, Protocol

class Expression(Protocol):
    def interpret(self, context: Dict[str, str]) -> None: ...

class PersonaExpr:
    def __init__(self, value: str) -> None:
        self.value = value.strip()

    def interpret(self, context: Dict[str, str]) -> None:
        context["persona"] = self.value

class TaskExpr:
    def __init__(self, value: str) -> None:
        self.value = value.strip()

    def interpret(self, context: Dict[str, str]) -> None:
        context["task"] = self.value

class LengthExpr:
    def __init__(self, value: str) -> None:
        self.value = value.strip()

    def interpret(self, context: Dict[str, str]) -> None:
        context["length"] = self.value

class FormatExpr:
    def __init__(self, value: str) -> None:
        self.value = value.strip()

    def interpret(self, context: Dict[str, str]) -> None:
        context["format"] = self.value

class ToneExpr:
    def __init__(self, value: str) -> None:
        self.value = value.strip()

    def interpret(self, context: Dict[str, str]) -> None:
        context["tone"] = self.value

class SourceExpr:
    def __init__(self, value: str) -> None:
        self.value = value.strip()

    def interpret(self, context: Dict[str, str]) -> None:
        context["source"] = self.value