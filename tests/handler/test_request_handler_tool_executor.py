from metis.handler.request_handler import RequestHandler


class SpyMediator:
    def handle_request(self, user_id, user_input, save=False, undo=False):
        return "ok"


class SpyToolExecutor:
    def __init__(self):
        self.calls = []

    def execute_tool(self, tool_name, args=None, user=None, services=None):
        self.calls.append((tool_name, args, user, services))
        return "tool-result"


def test_request_handler_execute_tool_wrapper_delegates_to_tool_executor():
    """
    RequestHandler.execute_tool remains only as a compatibility wrapper.
    Tool execution itself belongs to ToolExecutor.
    """
    executor = SpyToolExecutor()
    handler = RequestHandler(
        mediator=SpyMediator(),
        tool_executor=executor,
    )

    assert handler.tool_executor is executor

    result = handler.execute_tool(
        "search_web",
        args={"query": "pinot"},
        user="u1",
        services="services",
    )

    assert result == "tool-result"
    assert executor.calls == [
        ("search_web", {"query": "pinot"}, "u1", "services")
    ]