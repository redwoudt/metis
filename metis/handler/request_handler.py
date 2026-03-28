import re
import logging
import json
from uuid import uuid4

from metis.components.session_manager import SessionManager
from metis.prompts.builders.prompt_builder import PromptBuilder
from metis.policy.rate_limit import RateLimitPolicy
from metis.policy.auth import AuthPolicy
from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager
from metis.exceptions import ToolExecutionError
from metis.dsl import interpret_prompt_dsl
from metis.config import Config
from metis.events import Event

from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager

from metis.commands import command_registry
from metis.commands.base import ToolContext
from metis.handlers.pipelines import build_light_pipeline, build_strict_pipeline

logger = logging.getLogger(__name__)


class RequestHandler:
    """
    Orchestrates:
      - session lifecycle
      - DSL parsing
      - state -> prompt selection
      - model selection
      - tool execution via Command + Chain-of-Responsibility pipeline
    """

    def __init__(
        self,
        strategy=None,
        policy=None,
        auth_policy=None,
        memory_manager=None,
        config=None,
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

    # ------------------------------------------------------------------
    # Tool execution entry point (Command + CoR)
    # ------------------------------------------------------------------
    def execute_tool(self, tool_name, args=None, user=None, services=None):
        """
        Resolve and execute a tool command through the handler pipeline.

        Shared services are injected into the ToolContext so that commands can
        access infrastructure such as scheduling, quota checks, logging, and
        other cross-cutting system services without depending on global state.
        """
        if tool_name not in command_registry:
            raise ToolExecutionError(f"Unknown tool '{tool_name}'")

        # Instantiate the requested command from the registry.
        command = command_registry[tool_name]()

        # Use the shared services container unless an override is supplied.
        # Tests can pass a custom services object here to keep execution isolated.
        services = services or Config.services()

        # Copy args defensively so downstream code can enrich them safely.
        safe_args = dict(args or {})

        # Support both calling styles:
        # - user passed explicitly to execute_tool(...)
        # - user already embedded in args
        if user is None:
            user = safe_args.get("user")
        if user is not None and "user" not in safe_args:
            safe_args["user"] = user

        # Build the shared execution context consumed by handlers and commands.
        context = ToolContext(
            command=command,
            args=safe_args,
            user=user,
            metadata={"allow_user_tools": True},
            services=services,
        )

        # Commands that affect external systems or persist work should flow
        # through the stricter pipeline so quota checks and audit logging still apply.
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

        services = Config.services()
        event_bus = getattr(services, "event_bus", None)
        correlation_id = str(uuid4())

        if event_bus is not None:
            event_bus.publish(
                Event.create(
                    event_type="prompt.received",
                    source="RequestHandler",
                    correlation_id=correlation_id,
                    payload={"user_input": user_input},
                    metadata={"user_id": user_id},
                )
            )

        try:
            self.policy.enforce(user_id, user_input)
            if self.auth_policy:
                self.auth_policy.enforce(user_id, user_input)

            session = self.session_manager.load_or_create(user_id)

            # Be defensive: older snapshots may not have these attributes.
            if not hasattr(session, "tool_preferences") or session.tool_preferences is None:
                session.tool_preferences = {}
            if not hasattr(session, "persona"):
                session.persona = ""
            if not hasattr(session, "tone"):
                session.tone = ""
            if not hasattr(session, "context"):
                session.context = ""
            if not hasattr(session, "state"):
                session.state = None

            engine = getattr(session, "engine", None)

            if engine is not None and not hasattr(engine, "preferences"):
                engine.preferences = {}
                # ---------------- Tool DSL (pre-parse) ----------------
                tool_name = None
                tool_args = {}

                tool_match = re.search(r"\[tool:\s*([^\]]+)\]", user_input or "")
                args_match = re.search(r"\[args:\s*(\{.*?\})\]", user_input or "")

                if tool_match:
                    tool_name = tool_match.group(1).strip()

                    if args_match:
                        try:
                            tool_args = json.loads(args_match.group(1))
                        except Exception:
                            tool_args = {}

            # ---------------- DSL ----------------
            dsl_ctx = {}
            try:
                blocks = re.findall(r"\[[^\[\]:]+:[^\[\]]+?\]", user_input or "")
                if blocks:
                    dsl_ctx = interpret_prompt_dsl("".join(blocks))
                    user_input = re.sub(
                        r"\[[^\[\]:]+:[^\[\]]+?\]",
                        "",
                        user_input or "",
                    ).strip()

                    if dsl_ctx.get("persona"):
                        session.persona = dsl_ctx["persona"]
                    if dsl_ctx.get("tone"):
                        session.tone = dsl_ctx["tone"]
            except Exception:
                logger.exception("[RequestHandler] DSL parse error")

            # ---------------- Tool selection ----------------
            tool_name = None
            tool_args = {}

            if "tool" in dsl_ctx:
                tool_name = dsl_ctx["tool"]
                tool_args = dsl_ctx.get("args", {}) or {}

            if "tool_call" in dsl_ctx:
                tc = dsl_ctx["tool_call"] or {}
                tool_name = tc.get("name")
                tool_args = tc.get("arguments", {}) or {}

            if tool_name:
                session.tool_preferences["tool_name"] = tool_name
                session.tool_preferences["tool_args"] = tool_args

            # ---------------- Model + Engine ----------------
            model_role = (
                str(dsl_ctx.get("task")).lower()
                if dsl_ctx.get("task")
                else "analysis"
            )

            # Align initial conversation state with DSL task (if provided)
            initial_state = None
            if dsl_ctx.get("task"):
                task = str(dsl_ctx.get("task")).lower()
                if task == "summarize":
                    from metis.states.summarizing import SummarizingState
                    initial_state = SummarizingState()

            model_client = ModelFactory.for_role(model_role, self.config)
            # Pass the shared EventBus into ModelManager so model lifecycle
            # events are published through the same observer infrastructure.
            model_manager = ModelManager(model_client, event_bus=event_bus)

            if engine is None:
                engine = ConversationEngine(model_manager=model_manager)
                engine.preferences = {}
                if initial_state is not None:
                    engine.set_state(initial_state)
                    engine._explicit_state = True
                session.engine = engine
            else:
                engine.set_model_manager(model_manager)
                if initial_state is not None:
                    engine.set_state(initial_state)
                    engine._explicit_state = True

            # Ensure downstream components can trace this request flow.
            engine.preferences["correlation_id"] = correlation_id

            # ---------------- Response generation strategy ----------------
            # If the user requested a response style via DSL (e.g. [style: detailed]),
            # select the matching generation strategy and attach it to the engine.
            #
            # This keeps state code unchanged: states call engine.generate_with_model(...)
            # and the engine delegates to the configured strategy.
            try:
                from metis.response.generation.selector import StrategySelector

                selector = StrategySelector()
                engine.response_strategy = selector.select(dsl_ctx, self.config)
            except Exception:
                # Keep request handling functional if the response package isn't present
                # or during partial refactors.
                pass
            # ---------------- Response rendering preferences ----------------
            # Copy optional rendering flags from the DSL context into engine preferences.
            # These are used by the response post-processing pipeline.
            if "safety_enabled" in dsl_ctx:
                engine.preferences["safety_enabled"] = bool(dsl_ctx["safety_enabled"])
            if "format_markdown" in dsl_ctx:
                engine.preferences["format_markdown"] = bool(dsl_ctx["format_markdown"])
            if "include_citations" in dsl_ctx:
                engine.preferences["include_citations"] = bool(dsl_ctx["include_citations"])
            # Inject tool executor
            engine.execute_tool = self.execute_tool
            engine.preferences.update(session.tool_preferences)

            # ---------------- State selection (strategy + DSL) ----------------
            # Strategy is the primary driver for state selection in tests; DSL can still
            # seed an initial state when no strategy override is present.
            strategy_state = None
            if self.strategy is not None:
                try:
                    strategy_state = self.strategy.determine_state_name(user_input, dsl_ctx)
                except Exception:
                    logger.exception("[RequestHandler] Strategy state selection failed")

            if strategy_state:
                # Strategy state names are typically lowercase (e.g. "greeting").
                # Resolve to a State class and mark as explicit so the engine doesn't override it.
                try:
                    module_name = str(strategy_state).replace("State", "").lower()
                    class_name = (
                        str(strategy_state)
                        if str(strategy_state).endswith("State")
                        else f"{str(strategy_state).capitalize()}State"
                    )
                    module = __import__(f"metis.states.{module_name}", fromlist=[class_name])
                    state_cls = getattr(module, class_name)
                    engine.set_state(state_cls())
                    engine._explicit_state = True
                except Exception as exc:
                    logger.debug(
                        "[RequestHandler] Failed to resolve strategy state '%s': %s",
                        strategy_state,
                        exc,
                    )

            # ---------------- Prompt / response ----------------
            # IMPORTANT: ConversationEngine + States expect the *raw user text*.
            # The states/templates are responsible for building a rendered prompt.
            response = engine.respond(user_input)
            if response is None:
                response = ""

            if event_bus is not None:
                event_bus.publish(
                    Event.create(
                        event_type="response.generated",
                        source="RequestHandler",
                        correlation_id=correlation_id,
                        payload={"response_length": len(response)},
                        metadata={"user_id": user_id},
                    )
                )

            # Keep session state in sync with the engine after transitions.
            if hasattr(engine, "state") and engine.state is not None:
                session.state = engine.state.__class__.__name__

            self.session_manager.save(user_id, session)
            return response

        except Exception as exc:
            if event_bus is not None:
                event_bus.publish(
                    Event.create(
                        event_type="response.failed",
                        source="RequestHandler",
                        correlation_id=correlation_id,
                        payload={
                            "error_type": exc.__class__.__name__,
                            "error_message": str(exc),
                        },
                        metadata={"user_id": user_id},
                        severity="ERROR",
                    )
                )
            raise