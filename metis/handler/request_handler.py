"""
RequestHandler is the Facade entry point that orchestrates a full GenAI user request lifecycle.

How it works:
- Enforces user access policies.
- Loads or creates a session.
- Executes tools to enrich the user prompt.
- Builds a prompt using a strategy.
- Selects a model and generates a response.
- Saves the result back to the session.

Expansion Ideas:
- Add logging and tracing hooks.
- Support batch requests or streaming responses.
- Allow custom routing based on org/user config.
- Extend orchestration with retry/fallback logic.
"""

from metis.components.session_manager import SessionManager
from metis.components.tool_executor import ToolExecutor
from metis.components.prompt_builder import PromptBuilder
from metis.components.model_manager import ModelManager
from metis.strategy.default import DefaultPromptStrategy
from metis.policy.rate_limit import RateLimitPolicy
from metis.policy.auth import AuthPolicy
from metis.exceptions import ToolExecutionError


class RequestHandler:
    def __init__(self, strategy=None, policy=None, tool_executor=None):
        self.session_manager = SessionManager()
        self.tool_executor = tool_executor or ToolExecutor()
        self.prompt_builder = PromptBuilder()
        self.model_manager = ModelManager()
        self.prompt_strategy = strategy or DefaultPromptStrategy()
        self.policy = policy or RateLimitPolicy()
        self.auth_policy = AuthPolicy()

    def handle_prompt(self, user_id, user_input):
        # Enforce policies
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        # Session handling
        session = self.session_manager.load_or_create(user_id)

        # Tool execution (if applicable)
        if "weather" in user_input.lower():
            try:
                weather_data = self.tool_executor.execute("weather", user_input)
                user_input += f"\n(Weather Info: {weather_data})"
            except Exception as e:
                raise ToolExecutionError(str(e))

        # Prompt construction
        prompt = self.prompt_strategy.build_prompt(session, user_input)

        # Model selection and response generation
        model = self.model_manager.select(session, prompt)
        response = model.generate(prompt)

        # Session save
        self.session_manager.save(user_id, session, prompt, response)
        return response
