import logging

from metis.commands import command_registry
from metis.commands.base import ToolContext
from metis.components.session_manager import SessionManager
from metis.config import Config
from metis.conversation_engine import ConversationEngine
from metis.exceptions import ToolExecutionError
from metis.handlers.pipelines import build_light_pipeline, build_strict_pipeline
from metis.memory.manager import MemoryManager
from metis.mediator import ConversationMediator
from metis.policy.rate_limit import RateLimitPolicy
from metis.prompts.builders.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class RequestHandler:
    """
    Thin request-facing façade.

    The request lifecycle is coordinated by ConversationMediator.
    Tool execution remains here temporarily for compatibility and will be
    extracted into ToolExecutor in the next PR.
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

    # ------------------------------------------------------------------
    # Tool execution entry point (Command + CoR)
    # ------------------------------------------------------------------
    def execute_tool(self, tool_name, args=None, user=None, services=None):
        """
        Resolve and execute a tool command through the handler pipeline.

        This remains on RequestHandler during PR3 for backward compatibility.
        PR4 will move this into a dedicated ToolExecutor collaborator.
        """
        if tool_name not in command_registry:
            raise ToolExecutionError(f"Unknown tool '{tool_name}'")

        command = command_registry[tool_name]()
        services = services or self.services or Config.services()
        safe_args = dict(args or {})

        if user is None:
            user = safe_args.get("user")
        if user is not None and "user" not in safe_args:
            safe_args["user"] = user

        context = ToolContext(
            command=command,
            args=safe_args,
            user=user,
            metadata={"allow_user_tools": True},
            services=services,
        )

        if tool_name in {"execute_sql", "schedule_task"} and services is not None:
            pipeline = build_strict_pipeline(
                services.quota,
                services.audit_logger,
            )
        else:
            pipeline = build_light_pipeline()

        return pipeline.handle(context).result

    # ------------------------------------------------------------------
    # Main request handling
    # ------------------------------------------------------------------
    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        logger.info("[handle_prompt] user_id='%s' input='%s'", user_id, user_input)
        return self.mediator.handle_request(
            user_id=user_id,
            user_input=user_input,
            save=save,
            undo=undo,
        )