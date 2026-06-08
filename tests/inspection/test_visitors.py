from metis.inspection.records import (
    ExecutionTrace,
    ModelCallRecord,
    PromptPlan,
    PromptSection,
    ResponseNode,
    ToolResultRecord,
)
from metis.inspection.visitors import (
    LatencyVisitor,
    PromptInspectionVisitor,
    TokenUsageVisitor,
)


def test_token_usage_visitor_counts_prompt_and_response_words():
    """TokenUsageVisitor should aggregate prompt and response text via tokenizer."""
    trace = ExecutionTrace(
        correlation_id="corr-1",
        user_id="user-1",
        prompt_plan=PromptPlan(
            sections=[PromptSection(name="user", role="user", content="hello metis")]
        ),
        response=ResponseNode(content="hello user"),
    )

    visitor = TokenUsageVisitor()
    trace.accept(visitor)

    assert visitor.prompt_tokens == 2
    assert visitor.response_tokens == 2
    assert visitor.total_tokens == 4


def test_latency_visitor_summarizes_recorded_durations():
    """LatencyVisitor should read existing timings without measuring time itself."""
    trace = ExecutionTrace(
        correlation_id="corr-1",
        user_id="user-1",
        tool_results=[ToolResultRecord(name="search", status="success", duration_ms=120)],
        model_call=ModelCallRecord(provider="mock", model="stub", latency_ms=300),
    )

    visitor = LatencyVisitor()
    trace.accept(visitor)

    assert visitor.total_latency_ms == 420
    assert visitor.slowest_component == ("model:mock:stub", 300)


def test_prompt_inspection_visitor_summarizes_sections():
    """PromptInspectionVisitor should expose section metadata, not builder internals."""
    trace = ExecutionTrace(
        correlation_id="corr-1",
        user_id="user-1",
        prompt_plan=PromptPlan(
            sections=[PromptSection(name="user", role="user", content="hello")]
        ),
    )

    visitor = PromptInspectionVisitor()
    trace.accept(visitor)

    assert visitor.sections == [
        {"name": "user", "role": "user", "characters": 5}
    ]
