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
        session_manager=None,
    ):
        self.session_manager = session_manager or SessionManager()
        self.prompt_builder = PromptBuilder()

        self.policy = policy or RateLimitPolicy()
        self.auth_policy = auth_policy

        # An empty MemoryManager has length zero and is therefore falsey.  It is
        # still the caller's intended caretaker and must not be replaced.
        self.memory_manager = (
            memory_manager if memory_manager is not None else MemoryManager()
        )
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
                memory_manager=self.memory_manager,
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
                memory_manager=self.memory_manager,
                services=self.services,
                engine_cls=ConversationEngine,
            )

    def execute_tool(self, tool_name, args=None, user=None, services=None):
        """
        Deprecated compatibility wrapper.

        Tool execution belongs to ToolExecutor. This method remains as a
        stable façade entry point for existing callers, but new code should
        depend on ToolExecutor directly.
        """
        return self.tool_executor.execute_tool(
            tool_name=tool_name,
            args=args,
            user=user,
            services=services or self.services,
        )

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        logger.info(
            "[handle_prompt] user_id='%s' input_length=%d",
            user_id,
            len(user_input or ""),
        )
        return self.mediator.handle_request(
            user_id=user_id,
            user_input=user_input,
            save=save,
            undo=undo,
        )

    def run(self, user_id, user_input, save=False, undo=False):
        """Run one request and return its immutable response and trace bundle."""
        logger.info("[run] user_id='%s' input_length=%d", user_id, len(user_input or ""))
        return self.mediator.run_request(
            user_id=user_id,
            user_input=user_input,
            save=save,
            undo=undo,
        )
