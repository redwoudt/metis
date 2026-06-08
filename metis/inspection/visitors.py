"""
Concrete instrumentation visitors for Mêtis.

Each visitor answers one operational question. They aggregate insight from the
inspection records, but they never mutate the runtime records themselves.
"""

from __future__ import annotations

from .records import (
    BaseVisitor,
    ModelCallRecord,
    PromptSection,
    ResponseNode,
    ToolCommandRecord,
    ToolResultRecord,
)


class SimpleTokenizer:
    """
    Minimal tokenizer used for tests and local examples.

    Production integrations can inject a provider/model-specific tokenizer into
    TokenUsageVisitor without changing traversal.
    """

    def count(self, text: str) -> int:
        return len((text or "").split())


class TokenUsageVisitor(BaseVisitor):
    """
    Aggregates prompt and response token usage.
    """

    def __init__(self, tokenizer=None):
        self.tokenizer = tokenizer or SimpleTokenizer()
        self.prompt_tokens = 0
        self.response_tokens = 0

    def visit_prompt_section(self, section: PromptSection) -> None:
        self.prompt_tokens += self.tokenizer.count(section.content)

    def visit_response_node(self, response: ResponseNode) -> None:
        self.response_tokens += self.tokenizer.count(response.content)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.response_tokens


class TraceVisitor(BaseVisitor):
    """
    Records a compact structural path for one execution trace.
    """

    def __init__(self):
        self.steps: list[str] = []

    def visit_prompt_section(self, section: PromptSection) -> None:
        self.steps.append(f"prompt:{section.name}")

    def visit_tool_command(self, command: ToolCommandRecord) -> None:
        self.steps.append(f"tool_command:{command.name}")

    def visit_tool_result(self, result: ToolResultRecord) -> None:
        self.steps.append(f"tool_result:{result.name}:{result.status}")

    def visit_model_call(self, call: ModelCallRecord) -> None:
        self.steps.append(f"model:{call.provider}:{call.model}")

    def visit_response_node(self, response: ResponseNode) -> None:
        self.steps.append("response")


class LatencyVisitor(BaseVisitor):
    """
    Aggregates timing values that were already recorded during execution.
    """

    def __init__(self):
        self.components: list[tuple[str, int]] = []

    def visit_tool_result(self, result: ToolResultRecord) -> None:
        if result.duration_ms is not None:
            self.components.append((f"tool:{result.name}", result.duration_ms))

    def visit_model_call(self, call: ModelCallRecord) -> None:
        if call.latency_ms is not None:
            self.components.append((f"model:{call.provider}:{call.model}", call.latency_ms))

    @property
    def total_latency_ms(self) -> int:
        return sum(duration for _, duration in self.components)

    @property
    def slowest_component(self) -> tuple[str, int] | None:
        return max(self.components, key=lambda item: item[1], default=None)


class PromptInspectionVisitor(BaseVisitor):
    """
    Summarizes prompt sections without exposing prompt-builder internals.
    """

    def __init__(self):
        self.sections: list[dict[str, str | int]] = []

    def visit_prompt_section(self, section: PromptSection) -> None:
        self.sections.append(
            {
                "name": section.name,
                "role": section.role,
                "characters": len(section.content or ""),
            }
        )
