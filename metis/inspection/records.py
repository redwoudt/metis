"""
Visitor-safe runtime records for Mêtis inspection.

These classes are deliberately separate from the runtime components that create
prompts, execute tools, call models, and render responses. They form the stable
inspection surface discussed in Chapter 13: visitors inspect these immutable
records instead of reaching into private component internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Visitor(Protocol):
    """
    Structural contract for all instrumentation visitors.

    A concrete visitor may implement every method directly, but most visitors in
    Mêtis should inherit from BaseVisitor and override only the methods they need.
    """

    def visit_execution_trace(self, trace: "ExecutionTrace") -> None: ...
    def visit_prompt_plan(self, plan: "PromptPlan") -> None: ...
    def visit_prompt_section(self, section: "PromptSection") -> None: ...
    def visit_tool_command(self, command: "ToolCommandRecord") -> None: ...
    def visit_tool_result(self, result: "ToolResultRecord") -> None: ...
    def visit_model_call(self, call: "ModelCallRecord") -> None: ...
    def visit_response_node(self, response: "ResponseNode") -> None: ...


class Visitable(Protocol):
    """
    Contract for records that can participate in Visitor traversal.
    """

    def accept(self, visitor: Visitor) -> None: ...


class BaseVisitor:
    """
    No-op base visitor.

    This keeps concrete visitors small. For example, a token visitor only needs
    to override prompt and response visits; all other visit methods safely do
    nothing.
    """

    def visit_execution_trace(self, trace: "ExecutionTrace") -> None: pass
    def visit_prompt_plan(self, plan: "PromptPlan") -> None: pass
    def visit_prompt_section(self, section: "PromptSection") -> None: pass
    def visit_tool_command(self, command: "ToolCommandRecord") -> None: pass
    def visit_tool_result(self, result: "ToolResultRecord") -> None: pass
    def visit_model_call(self, call: "ModelCallRecord") -> None: pass
    def visit_response_node(self, response: "ResponseNode") -> None: pass


@dataclass(frozen=True)
class PromptSection:
    """
    One inspectable section of the final prompt.

    The content is included because token accounting and prompt inspection need
    it, but callers can redact or omit content before constructing the record if
    they are running in a restricted inspection mode.
    """

    name: str
    role: str
    content: str

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_prompt_section(self)


@dataclass(frozen=True)
class PromptPlan:
    """
    Inspectable prompt structure for a request.

    PromptPlan owns traversal to its child PromptSection records, but it does not
    perform any instrumentation itself.
    """

    sections: list[PromptSection] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_prompt_plan(self)
        for section in self.sections:
            section.accept(visitor)


@dataclass(frozen=True)
class ToolCommandRecord:
    """
    Visitor-safe record of the user's intended tool call.
    """

    name: str
    args: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_tool_command(self)


@dataclass(frozen=True)
class ToolResultRecord:
    """
    Visitor-safe record of a completed tool execution.

    duration_ms is optional so the first integration can capture tool intent even
    before every tool path records timing data.
    """

    name: str
    status: str
    duration_ms: int | None = None
    output_summary: str = ""

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_tool_result(self)


@dataclass(frozen=True)
class ModelCallRecord:
    """
    Visitor-safe summary of a model call.

    This deliberately stores stable metadata instead of provider SDK objects,
    credentials, transport state, or retry internals.
    """

    provider: str
    model: str
    prompt_length: int = 0
    response_length: int = 0
    latency_ms: int | None = None

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_model_call(self)


@dataclass(frozen=True)
class ResponseNode:
    """
    Inspectable response node.

    Children support decorated or composed responses while keeping traversal
    uniform for simple and nested response structures.
    """

    content: str
    children: list["ResponseNode"] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_response_node(self)
        for child in self.children:
            child.accept(visitor)


@dataclass(frozen=True)
class ExecutionTrace:
    """
    Request-level entry point for Visitor traversal.

    The mediator assembles this record after execution. Visitors start here and
    move through whichever runtime records were produced for the request.
    """

    correlation_id: str
    user_id: str
    prompt_plan: PromptPlan | None = None
    tool_commands: list[ToolCommandRecord] = field(default_factory=list)
    tool_results: list[ToolResultRecord] = field(default_factory=list)
    model_call: ModelCallRecord | None = None
    response: ResponseNode | None = None

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_execution_trace(self)

        if self.prompt_plan is not None:
            self.prompt_plan.accept(visitor)

        for command in self.tool_commands:
            command.accept(visitor)

        for result in self.tool_results:
            result.accept(visitor)

        if self.model_call is not None:
            self.model_call.accept(visitor)

        if self.response is not None:
            self.response.accept(visitor)
