import logging

from metis.components.session_manager import SessionManager
from metis.config import Config
from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager
from metis.mediator import ConversationMediator
from metis.policy.rate_limit import RateLimitPolicy
from metis.prompts.builders.prompt_builder import PromptBuilder
from metis.tools import ToolExecutor

logger = logging.getLogger(__name__)


class RequestHandler:
    """
    Thin request-facing façade.

    The request lifecycle is coordinated by ConversationMediator.
    Tool execution is delegated to ToolExecutor.
    """

    def __init__(
        self,
        strategy=None,
        policy=None,
        auth_policy=None,
        memory_manager=None,
        config=None,
        mediator=None,
        services=None,
        tool_executor=None,
    ):
        self.session_manager = SessionManager()
        self.prompt_builder = PromptBuilder()

        self.policy = policy or RateLimitPolicy()
        self.auth_policy = auth_policy

        self.memory_manager = memory_manager or MemoryManager()
        self.strategy = strategy

        self.config = config or {
            "vendor": getattr(Config, "DEFAULT_VENDOR", "openai"),
            "model": getattr(Config, "DEFAULT_MODEL", "gpt-4o-mini"),
            "policies": getattr(Config, "MODEL_POLICIES", {}),
        }

        self.services = services or Config.services()
        self.tool_executor = (
            tool_executor
            or getattr(self.services, "tool_executor", None)
            or ToolExecutor(services=self.services)
        )

        if mediator is not None:
            self.mediator = mediator
        elif hasattr(self.services, "build_conversation_mediator"):
            self.mediator = self.services.build_conversation_mediator(
                session_manager=self.session_manager,
                policy=self.policy,
                auth_policy=self.auth_policy,
                strategy=self.strategy,
                config=self.config,
                request_handler=self,
                engine_cls=ConversationEngine,
            )
        else:
            self.mediator = ConversationMediator(
                session_manager=self.session_manager,
                policy=self.policy,
                auth_policy=self.auth_policy,
                strategy=self.strategy,
                config=self.config,
                request_handler=self,
                services=self.services,
                engine_cls=ConversationEngine,
            )

    def execute_tool(self, tool_name, args=None, user=None, services=None):
        """
        Backward-compatible wrapper.

        Tool execution now belongs to ToolExecutor. This method remains so
        existing callers and tests can migrate gradually.
        """
        return self.tool_executor.execute_tool(
            tool_name=tool_name,
            args=args,
            user=user,
            services=services or self.services,
        )

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        logger.info("[handle_prompt] user_id='%s' input='%s'", user_id, user_input)
        return self.mediator.handle_request(
            user_id=user_id,
            user_input=user_input,
            save=save,
            undo=undo,
        )