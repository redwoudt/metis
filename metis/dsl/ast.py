from dataclasses import dataclass
from typing import Any, Dict
import json


class Expression:
    def interpret(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError()


@dataclass
class PersonaExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["persona"] = self.value


@dataclass
class TaskExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["task"] = self.value


@dataclass
class LengthExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["length"] = self.value


@dataclass
class FormatExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["format"] = self.value


@dataclass
class ToneExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["tone"] = self.value


@dataclass
class SourceExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["source"] = self.value


# ----------------------------
# Tool execution expressions
# ----------------------------

@dataclass
class ToolExpr(Expression):
    value: str
    def interpret(self, context: Dict[str, Any]) -> None:
        context["tool"] = self.value


@dataclass
class ArgsExpr(Expression):
    raw: str

    def interpret(self, context: Dict[str, Any]) -> None:
        # args is expected to be JSON (e.g. {"query":"pinot"})
        # If it's invalid JSON, keep the raw string so downstream can decide what to do.
        try:
            parsed = json.loads(self.raw)
            if isinstance(parsed, dict):
                context["args"] = parsed
            else:
                context["args"] = {"value": parsed}
        except Exception:
            context["args"] = {"raw": self.raw}


@dataclass
class ToolCallExpr(Expression):
    raw: str

    def interpret(self, context: Dict[str, Any]) -> None:
        # tool_call is expected to be JSON (e.g. {"name":"search_web","args":{"query":"pinot"}})
        try:
            parsed = json.loads(self.raw)
            if isinstance(parsed, dict):
                context["tool_call"] = parsed
            else:
                context["tool_call"] = {"value": parsed}
        except Exception:
            context["tool_call"] = {"raw": self.raw}