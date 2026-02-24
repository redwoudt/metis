from dataclasses import dataclass
from typing import Any, Dict
import json


def _parse_bool(value: str) -> bool:
    """Parse common DSL boolean values.

    Supports: true/false, yes/no, on/off, 1/0 (case-insensitive).
    Any unrecognized value defaults to False.
    """
    v = (value or "").strip().lower()
    if v in {"true", "yes", "y", "on", "1"}:
        return True
    if v in {"false", "no", "n", "off", "0"}:
        return False
    return False


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


@dataclass
class StyleExpr(Expression):
    value: str

    def interpret(self, context: Dict[str, Any]) -> None:
        # Stores the requested response style in the shared DSL context.
        # Example usage in DSL:
        #   [style: detailed]
        # The actual selection logic is handled elsewhere.
        context["style"] = self.value


@dataclass
class SafetyEnabledExpr(Expression):
    value: str

    def interpret(self, context: Dict[str, Any]) -> None:
        # Enables or disables optional safety post-processing.
        # Accepts common truthy/falsey strings to keep the DSL ergonomic.
        context["safety_enabled"] = _parse_bool(self.value)


@dataclass
class FormatMarkdownExpr(Expression):
    value: str

    def interpret(self, context: Dict[str, Any]) -> None:
        # When enabled, the response renderer may wrap output in Markdown.
        context["format_markdown"] = _parse_bool(self.value)


@dataclass
class IncludeCitationsExpr(Expression):
    value: str

    def interpret(self, context: Dict[str, Any]) -> None:
        # When enabled, the response renderer may append a citation footer.
        context["include_citations"] = _parse_bool(self.value)


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