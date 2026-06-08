from metis.handler.request_handler import RequestHandler
from metis.inspection.service import InspectionService
from metis.inspection.visitors import TraceVisitor


def test_inspection_service_runs_visitor_over_trace():
    """InspectionService should centralize visitor execution."""
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    handler.handle_prompt("user-1", "hello")

    trace = handler.mediator.last_execution_trace
    visitor = InspectionService().run(trace, TraceVisitor())

    assert "prompt:user_input" in visitor.steps
    assert "response" in visitor.steps


def test_mediator_builds_execution_trace_after_request():
    """ConversationMediator should expose a visitor-safe trace after execution."""
    handler = RequestHandler(config={"vendor": "mock", "model": "stub", "policies": {}})
    handler.handle_prompt("user-1", "hello")

    trace = handler.mediator.last_execution_trace

    assert trace is not None
    assert trace.user_id == "user-1"
    assert trace.prompt_plan is not None
    assert trace.model_call is not None
    assert trace.response is not None
