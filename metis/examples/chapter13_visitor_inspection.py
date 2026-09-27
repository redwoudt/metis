"""Inspect one deterministic Mêtis execution trace with focused visitors."""

from __future__ import annotations

from metis.inspection import (
    ExecutionTrace,
    InspectionService,
    ModelCallRecord,
    PromptPlan,
    PromptSection,
    ResponseNode,
    ToolCommandRecord,
    ToolResultRecord,
)


def build_trace() -> ExecutionTrace:
    """Create a provider-free trace that exercises every inspection record."""
    return ExecutionTrace(
        correlation_id="chapter13-demo",
        user_id="reader-13",
        prompt_plan=PromptPlan(
            sections=[
                PromptSection(
                    name="system",
                    role="system",
                    content="Answer with concise, sourced facts.",
                ),
                PromptSection(
                    name="user",
                    role="user",
                    content="Find the weather for Ithaca.",
                ),
            ]
        ),
        tool_commands=[
            ToolCommandRecord(name="weather.lookup", args={"city": "Ithaca"})
        ],
        tool_results=[
            ToolResultRecord(
                name="weather.lookup",
                status="success",
                duration_ms=34,
                output_summary="clear, 18 C",
            )
        ],
        model_call=ModelCallRecord(
            provider="mock",
            model="chapter13",
            prompt_length=64,
            response_length=26,
            latency_ms=121,
        ),
        response=ResponseNode(content="Ithaca is clear and mild."),
    )


def run_demo() -> dict[str, str | int]:
    """Run four focused visitors over the same completed request trace."""
    trace = build_trace()
    inspection = InspectionService()

    path = inspection.trace(trace).steps
    tokens = inspection.tokens(trace)
    latency = inspection.latency(trace)
    prompt = inspection.prompt(trace)
    slowest_name, slowest_ms = latency.slowest_component or ("none", 0)

    return {
        "steps": " > ".join(path),
        "tokens": tokens.total_tokens,
        "latency_ms": latency.total_latency_ms,
        "slowest": f"{slowest_name}:{slowest_ms}",
        "prompt_sections": len(prompt.sections),
    }


def main() -> int:
    """Print the stable summary used in Chapter 13."""
    for key, value in run_demo().items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
