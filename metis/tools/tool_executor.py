# tools/tool_executor.py

class ToolExecutor:
    """
    Dummy executor to simulate tool usage in ExecutingState.
    Could be extended to call APIs, retrieve data, or perform local actions.
    """

    def run(self, user_input):
        """
        Simulate a task execution.

        :param user_input: Task instruction from the user.
        :return: Simulated result.
        """
        return f"Tool executed with: '{user_input}'"