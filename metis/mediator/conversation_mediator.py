import logging
import re
from typing import Any

from metis.components.model_manager import ModelManager
from metis.config import Config
from metis.dsl import interpret_prompt_dsl
from metis.events import Event
from metis.models.model_factory import ModelFactory

from .context import RequestContext

logger = logging.getLogger(__name__)


class ConversationMediator:
    """
    Coordinates the request lifecycle for Mêtis.

    The mediator owns sequencing. It delegates actual work to existing
    collaborators such as SessionManager, DSL interpreter, ModelFactory,
    ModelManager, ConversationEngine, and state objects.
    """

    def __init__(
            self,
            session_manager: Any = None,
            policy: Any = None,
            auth_policy: Any = None,
            strategy: Any = None,
            config: dict | None = None,
            request_handler: Any = None,
            services: Any = None,
            engine_cls: Any = None,
    ):
        self.session_manager = session_manager
        self.policy = policy
        self.auth_policy = auth_policy
        self.strategy = strategy
        self.config = config or {
            "vendor": getattr(Config, "DEFAULT_VENDOR", "openai"),
            "model": getattr(Config, "DEFAULT_MODEL", "gpt-4o-mini"),
            "policies": getattr(Config, "MODEL_POLICIES", {}),
        }
        self.request_handler = request_handler
        self.services = services
        if engine_cls is None:
            from metis.conversation_engine import ConversationEngine

            engine_cls = ConversationEngine

        self.engine_cls = engine_cls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def handle_request(
        self,
        user_id: str,
        user_input: str,
        save: bool = False,
        undo: bool = False,
    ) -> str:
        context = self.prepare_context(
            user_id=user_id,
            user_input=user_input,
            save=save,
            undo=undo,
        )

        try:
            self.publish_prompt_received(context)
            self.enforce_policies(context)
            self.load_session(context)
            self.normalise_session(context)
            self.parse_dsl(context)
            self.select_tool(context)
            self.select_model(context)
            self.configure_engine(context)
            self.configure_response_strategy(context)
            self.apply_rendering_preferences(context)
            self.apply_state_strategy(context)
            self.execute_turn(context)
            self.publish_response_generated(context)
            self.persist_session(context)
            return context.response

        except Exception as exc:
            self.publish_response_failed(context, exc)
            raise

    # ------------------------------------------------------------------
    # Lifecycle steps
    # ------------------------------------------------------------------
    def prepare_context(
        self,
        user_id: str,
        user_input: str,
        save: bool = False,
        undo: bool = False,
    ) -> RequestContext:
        services = self.services
        if services is None:
            try:
                services = Config.services()
            except Exception:
                services = None

        event_bus = getattr(services, "event_bus", None) if services is not None else None

        return RequestContext(
            user_id=user_id,
            user_input=user_input,
            clean_input=user_input,
            save=save,
            undo=undo,
            services=services,
            event_bus=event_bus,
        )

    def publish_prompt_received(self, context: RequestContext) -> None:
        if context.event_bus is None:
            return

        context.event_bus.publish(
            Event.create(
                event_type="prompt.received",
                source="ConversationMediator",
                correlation_id=context.correlation_id,
                payload={"user_input": context.user_input},
                metadata={"user_id": context.user_id},
            )
        )

    def enforce_policies(self, context: RequestContext) -> None:
        if self.policy is not None:
            self.policy.enforce(context.user_id, context.user_input)

        if self.auth_policy is not None:
            self.auth_policy.enforce(context.user_id, context.user_input)

    def load_session(self, context: RequestContext) -> None:
        if self.session_manager is None:
            raise RuntimeError("ConversationMediator requires a session_manager")

        context.session = self.session_manager.load_or_create(context.user_id)

    def normalise_session(self, context: RequestContext) -> None:
        session = context.session

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

        context.engine = getattr(session, "engine", None)

    def parse_dsl(self, context: RequestContext) -> None:
        try:
            blocks = re.findall(
                r"\[[^\[\]:]+:[^\[\]]+?\]",
                context.user_input or "",
            )
            if not blocks:
                context.dsl_context = {}
                context.clean_input = context.user_input
                return

            dsl_ctx = interpret_prompt_dsl("".join(blocks))
            context.dsl_context = dict(dsl_ctx)

            context.clean_input = re.sub(
                r"\[[^\[\]:]+:[^\[\]]+?\]",
                "",
                context.user_input or "",
            ).strip()

            if context.dsl_context.get("persona"):
                context.session.persona = context.dsl_context["persona"]
            if context.dsl_context.get("tone"):
                context.session.tone = context.dsl_context["tone"]

        except Exception:
            logger.exception("[ConversationMediator] DSL parse error")
            context.dsl_context = {}
            context.clean_input = context.user_input

    def select_tool(self, context: RequestContext) -> None:
        dsl_ctx = context.dsl_context or {}

        tool_name = None
        tool_args = {}

        if "tool" in dsl_ctx:
            tool_name = dsl_ctx["tool"]
            tool_args = dsl_ctx.get("args", {}) or {}

        if "tool_call" in dsl_ctx:
            tool_call = dsl_ctx["tool_call"] or {}
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {}) or {}

        context.tool_name = tool_name
        context.tool_args = tool_args or {}

        if tool_name:
            context.session.tool_preferences["tool_name"] = tool_name
            context.session.tool_preferences["tool_args"] = context.tool_args

    def select_model(self, context: RequestContext) -> None:
        dsl_ctx = context.dsl_context or {}

        context.model_role = (
            str(dsl_ctx.get("task")).lower()
            if dsl_ctx.get("task")
            else "analysis"
        )

        if dsl_ctx.get("task"):
            task = str(dsl_ctx.get("task")).lower()
            if task == "summarize":
                from metis.states.summarizing import SummarizingState

                context.initial_state = SummarizingState()

        context.model_client = ModelFactory.for_role(context.model_role, self.config)
        context.model_manager = ModelManager(
            context.model_client,
            event_bus=context.event_bus,
        )

    def configure_engine(self, context: RequestContext) -> None:
        session = context.session
        engine = context.engine

        if engine is None:
            engine = self.engine_cls(model_manager=context.model_manager)
            engine.preferences = {}

            if context.initial_state is not None:
                engine.set_state(context.initial_state)
                engine._explicit_state = True

            session.engine = engine
        else:
            if not hasattr(engine, "preferences") or engine.preferences is None:
                engine.preferences = {}

            engine.set_model_manager(context.model_manager)

            if context.initial_state is not None:
                engine.set_state(context.initial_state)
                engine._explicit_state = True

        engine.preferences["correlation_id"] = context.correlation_id
        engine.services = context.services
        engine.event_bus = context.event_bus
        engine.user_id = context.user_id

        if context.services is not None:
            engine.tool_executor = getattr(context.services, "tool_executor", None)

        if getattr(engine, "tool_executor", None) is None and self.request_handler is not None:
            engine.tool_executor = getattr(self.request_handler, "tool_executor", None)

        engine.preferences.update(session.tool_preferences)

        context.engine = engine

    def configure_response_strategy(self, context: RequestContext) -> None:
        try:
            from metis.response.generation.selector import StrategySelector

            selector = StrategySelector()
            context.engine.response_strategy = selector.select(
                context.dsl_context,
                self.config,
            )
        except Exception:
            logger.exception("[ConversationMediator] Response strategy selection failed")

    def apply_rendering_preferences(self, context: RequestContext) -> None:
        dsl_ctx = context.dsl_context or {}
        preferences = context.engine.preferences

        if "safety_enabled" in dsl_ctx:
            preferences["safety_enabled"] = bool(dsl_ctx["safety_enabled"])
        if "format_markdown" in dsl_ctx:
            preferences["format_markdown"] = bool(dsl_ctx["format_markdown"])
        if "include_citations" in dsl_ctx:
            preferences["include_citations"] = bool(dsl_ctx["include_citations"])

    def apply_state_strategy(self, context: RequestContext) -> None:
        if self.strategy is None:
            return

        try:
            strategy_state = self.strategy.determine_state_name(
                context.clean_input,
                context.dsl_context,
            )
        except Exception:
            logger.exception("[ConversationMediator] Strategy state selection failed")
            return

        if not strategy_state:
            return

        try:
            module_name = str(strategy_state).replace("State", "").lower()
            class_name = (
                str(strategy_state)
                if str(strategy_state).endswith("State")
                else f"{str(strategy_state).capitalize()}State"
            )

            module = __import__(
                f"metis.states.{module_name}",
                fromlist=[class_name],
            )
            state_cls = getattr(module, class_name)

            context.engine.set_state(state_cls())
            context.engine._explicit_state = True

        except Exception as exc:
            logger.debug(
                "[ConversationMediator] Failed to resolve strategy state '%s': %s",
                strategy_state,
                exc,
            )

    def execute_turn(self, context: RequestContext) -> None:
        response = context.engine.respond(context.clean_input)

        if response is None:
            response = ""

        context.response = response

        if hasattr(context.engine, "state") and context.engine.state is not None:
            context.session.state = context.engine.state.__class__.__name__

    def publish_response_generated(self, context: RequestContext) -> None:
        if context.event_bus is None:
            return

        context.event_bus.publish(
            Event.create(
                event_type="response.generated",
                source="ConversationMediator",
                correlation_id=context.correlation_id,
                payload={"response_length": len(context.response)},
                metadata={"user_id": context.user_id},
            )
        )

    def persist_session(self, context: RequestContext) -> None:
        self.session_manager.save(context.user_id, context.session)

    def publish_response_failed(self, context: RequestContext, exc: Exception) -> None:
        if context.event_bus is None:
            return

        context.event_bus.publish(
            Event.create(
                event_type="response.failed",
                source="ConversationMediator",
                correlation_id=context.correlation_id,
                payload={
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                },
                metadata={"user_id": context.user_id},
                severity="ERROR",
            )
        )