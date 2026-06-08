from metis.inspection.records import (
    ExecutionTrace,
    ModelCallRecord,
    PromptPlan,
    PromptSection,
    ResponseNode,
)
from metis.inspection.visitors import TraceVisitor


def test_execution_trace_traverses_prompt_model_and_response():
    """Visitor traversal should start at ExecutionTrace and visit child records."""
    trace = ExecutionTrace(
        correlation_id="corr-1",
        user_id="user-1",
        prompt_plan=PromptPlan(
            sections=[
                PromptSection(name="system", role="system", content="Be helpful."),
                PromptSection(name="user", role="user", content="Hello"),
            ]
        ),
        model_call=ModelCallRecord(provider="mock", model="stub"),
        response=ResponseNode(content="Hi there"),
    )

    visitor = TraceVisitor()
    trace.accept(visitor)

    assert visitor.steps == [
        "prompt:system",
        "prompt:user",
        "model:mock:stub",
        "response",
    ]
