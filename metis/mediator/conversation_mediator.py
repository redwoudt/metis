import logging
import re
from typing import Any

from metis.components.model_manager import ModelManager
from metis.config import Config
from metis.dsl import interpret_prompt_dsl
from metis.events import Event, content_summary, exception_summary
from metis.models.model_factory import ModelFactory

from .context import RequestContext
from .result import RequestResult

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
            behavior_strategy: Any = None,
            model_resolver: Any = None,
            config: dict | None = None,
            request_handler: Any = None,
            memory_manager: Any = None,
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
        if behavior_strategy is None:
            from metis.behavior import build_default_behavior_strategy

            behavior_strategy = build_default_behavior_strategy(self.config)
        self.behavior_strategy = behavior_strategy
        self.model_resolver = model_resolver or ModelFactory.for_role
        self.request_handler = request_handler
        self.memory_manager = memory_manager
        self.services = services
        if engine_cls is None:
            from metis.conversation_engine import ConversationEngine

            engine_cls = ConversationEngine

        self.engine_cls = engine_cls

        # Compatibility-only local debugging surface. Concurrent and production
        # callers should consume RequestResult.execution_trace instead.
        self.last_execution_trace = None

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
        """Compatibility façade returning only the generated response text."""
        return self.run_request(
            user_id=user_id,
            user_input=user_input,
            save=save,
            undo=undo,
        ).response

    def run_request(
        self,
        user_id: str,
        user_input: str,
        save: bool = False,
        undo: bool = False,
    ) -> RequestResult:
        """Run the complete request lifecycle and return a request-scoped result."""
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
            self.resolve_behavior(context)
            self.select_tool(context)
            self.select_model(context)
            self.configure_engine(context)
            self.restore_if_requested(context)
            self.configure_response_strategy(context)
            self.apply_rendering_preferences(context)
            self.apply_state_strategy(context)
            self.execute_turn(context)
            self.checkpoint_if_requested(context)

            # Visitor integration point: build one immutable inspection record
            # after execution, so visitors can inspect the completed request
            # without running inside the runtime components themselves.
            context.execution_trace = self.build_execution_trace(context)
            self.last_execution_trace = context.execution_trace

            self.publish_response_generated(context)
            self.persist_session(context)
            return RequestResult(
                response=context.response,
                correlation_id=context.correlation_id,
                execution_trace=context.execution_trace,
                checkpoint_saved=context.checkpoint_saved,
                checkpoint_restored=context.checkpoint_restored,
            )

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
                payload=content_summary(context.user_input),
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

        plan = context.behavior_plan
        if tool_name and plan is not None and not plan.allow_tools:
            raise PermissionError(
                f"Behavior template '{plan.name}' does not allow tool execution"
            )

        context.tool_name = tool_name
        context.tool_args = tool_args or {}

        if tool_name:
            context.session.tool_preferences["tool_name"] = tool_name
            context.session.tool_preferences["tool_args"] = context.tool_args

            # Record the intended tool command for Visitor inspection.
            # This captures the request structure without coupling ToolExecutor
            # or the command handlers to instrumentation visitors.
            from metis.inspection.records import ToolCommandRecord

            context.inspection_tool_commands.append(
                ToolCommandRecord(
                    name=str(tool_name),
                    args=(
                        dict(context.tool_args or {})
                        if self.config.get("inspection_include_content", False)
                        else {
                            str(name): "<redacted>"
                            for name in sorted(context.tool_args or {})
                        }
                    ),
                )
            )

    def select_model(self, context: RequestContext) -> None:
        dsl_ctx = context.dsl_context or {}

        plan = context.behavior_plan
        task_role = str(dsl_ctx.get("task", "")).strip().lower()
        registered_roles = getattr(Config, "MODEL_REGISTRY", {})
        if plan is not None and plan.name != "balanced":
            context.model_role = plan.model_role
        elif task_role and task_role in registered_roles:
            # Preserve the role-selection contract introduced in Chapter 6.
            context.model_role = task_role
        elif plan is not None:
            context.model_role = plan.model_role
        else:
            context.model_role = task_role or "analysis"

        if dsl_ctx.get("task"):
            task = str(dsl_ctx.get("task")).lower()
            if task == "summarize":
                from metis.states.summarizing import SummarizingState

                context.initial_state = SummarizingState()

        context.model_client = self.model_resolver(context.model_role, self.config)
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
        engine.inspection_tool_results = context.inspection_tool_results

        if context.services is not None:
            engine.tool_executor = getattr(context.services, "tool_executor", None)

        if getattr(engine, "tool_executor", None) is None and self.request_handler is not None:
            engine.tool_executor = getattr(self.request_handler, "tool_executor", None)

        # Session-level presentation preferences and per-request DSL overrides
        # must reach the engine before the state renders its prompt.
        stored_preferences = getattr(session, "preferences", {}) or {}
        for name in ("tone", "persona", "context"):
            value = getattr(session, name, None)
            if value in (None, ""):
                value = stored_preferences.get(name)
            if value not in (None, ""):
                engine.preferences[name] = value

        engine.preferences.update(session.tool_preferences)

        context.engine = engine

    def restore_if_requested(self, context: RequestContext) -> None:
        """Restore the latest checkpoint for this user before current preferences."""
        if not context.undo:
            return
        if self.memory_manager is None:
            raise RuntimeError("Undo requires an injected MemoryManager")

        try:
            restored = self.memory_manager.restore_into(
                context.engine,
                scope=context.user_id,
            )
        except TypeError:
            # Compatibility for user-supplied Chapter 14 caretakers.
            restored = self.memory_manager.restore_into(context.engine)
        if not restored:
            raise LookupError("No checkpoint is available for this conversation")

        # Checkpoints contain conversation state, never live infrastructure.
        context.engine.set_model_manager(context.model_manager)
        context.engine.services = context.services
        context.engine.event_bus = context.event_bus
        context.engine.user_id = context.user_id
        context.engine.inspection_tool_results = context.inspection_tool_results
        if context.services is not None:
            context.engine.tool_executor = getattr(
                context.services,
                "tool_executor",
                context.engine.tool_executor,
            )
        context.engine.preferences["correlation_id"] = context.correlation_id
        context.session.engine = context.engine
        context.session.history = context.engine.history
        context.checkpoint_restored = True

    def checkpoint_if_requested(self, context: RequestContext) -> None:
        """Create a lean checkpoint only after a successful turn."""
        if not context.save:
            return
        if self.memory_manager is None:
            raise RuntimeError("Checkpointing requires an injected MemoryManager")

        memento = context.engine.create_memento(
            self.memory_manager.artifact_pool,
            tenant_id=context.user_id,
            model_role=context.model_role,
        )
        try:
            self.memory_manager.save(memento, scope=context.user_id)
        except TypeError:
            # Compatibility for user-supplied Chapter 14 caretakers.
            self.memory_manager.save(memento)
        context.session.history = context.engine.history
        context.checkpoint_saved = True

    def configure_response_strategy(self, context: RequestContext) -> None:
        try:
            from metis.response.generation.selector import StrategySelector

            selector = StrategySelector()
            dsl_context = context.dsl_context
            plan = context.behavior_plan
            if plan is not None and (
                dsl_context.get("behavior") or plan.name != "balanced"
            ):
                dsl_context = {
                    **dsl_context,
                    "style": plan.response_style,
                }
            context.engine.response_strategy = selector.select(dsl_context, self.config)
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

        plan = context.behavior_plan
        if plan is not None:
            if plan.require_safety:
                preferences["safety_enabled"] = True
            if plan.include_citations:
                preferences["include_citations"] = True

    def resolve_behavior(self, context: RequestContext) -> None:
        from metis.behavior import BehaviorContext

        dsl_ctx = context.dsl_context or {}
        task = str(dsl_ctx.get("task", "")).strip().lower()
        high_risk_tasks = {
            str(item).strip().lower()
            for item in self.config.get(
                "high_risk_tasks",
                {"medical", "legal", "financial", "safety"},
            )
        }
        risk = "high" if task in high_risk_tasks else str(
            self.config.get("risk", "normal")
        )

        context.behavior_plan = self.behavior_strategy.choose(
            BehaviorContext(
                requested_template=dsl_ctx.get("behavior"),
                configured_default=self.config.get("behavior_template"),
                risk=risk,
            )
        )

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
        # A tool may have been selected on an earlier conversational turn and
        # executed only when the State machine reaches ExecutingState.  Record
        # that active intent in the same request trace as its outcome.
        from metis.states.executing import ExecutingState

        if (
            isinstance(getattr(context.engine, "state", None), ExecutingState)
            and not context.inspection_tool_commands
        ):
            tool_name = context.engine.preferences.get("tool_name")
            tool_args = context.engine.preferences.get("tool_args") or {}
            if tool_name:
                from metis.inspection.records import ToolCommandRecord

                context.inspection_tool_commands.append(
                    ToolCommandRecord(
                        name=str(tool_name),
                        args=(
                            dict(tool_args)
                            if self.config.get("inspection_include_content", False)
                            else {
                                str(name): "<redacted>"
                                for name in sorted(tool_args)
                            }
                        ),
                    )
                )

        response = context.engine.respond(context.clean_input)

        if response is None:
            response = ""

        context.response = response

        if hasattr(context.engine, "state") and context.engine.state is not None:
            context.session.state = context.engine.state.__class__.__name__

    def build_prompt_plan_record(self, context: RequestContext):
        """
        Build a visitor-safe prompt record from the request context.

        This first implementation records the cleaned user input and any parsed
        DSL context. Later chapters can enrich this with the full PromptBuilder
        output without changing the Visitor interfaces.
        """
        from metis.inspection.records import PromptPlan, PromptSection

        include_content = bool(
            self.config.get("inspection_include_content", False)
        )

        sections = [
            PromptSection(
                name="user_input",
                role="user",
                content=(context.clean_input or "") if include_content else "",
            )
        ]

        if context.dsl_context:
            sections.append(
                PromptSection(
                    name="dsl_context",
                    role="system",
                    content=str(context.dsl_context) if include_content else "",
                )
            )

        return PromptPlan(sections=sections)

    def build_model_call_record(self, context: RequestContext):
        """
        Build a visitor-safe model call summary.

        The record intentionally captures stable metadata only. It does not expose
        provider SDK clients, credentials, transport state, or retry internals.
        """
        from metis.inspection.records import ModelCallRecord

        model_client = context.model_client
        provider = self._read_metadata(
            model_client,
            ("provider", "vendor"),
            type(model_client).__name__,
        )
        model = self._read_metadata(
            model_client,
            ("model", "model_name"),
            type(model_client).__name__,
        )

        return ModelCallRecord(
            provider=str(provider),
            model=str(model),
            prompt_length=len(context.clean_input or ""),
            response_length=len(context.response or ""),
        )

    @staticmethod
    def _read_metadata(source: Any, names: tuple[str, ...], default: str) -> str:
        """Normalize adapter/proxy metadata exposed as either values or methods."""
        for name in names:
            value = getattr(source, name, None)
            if callable(value):
                try:
                    value = value()
                except Exception:
                    value = None
            if value not in (None, ""):
                return str(value)
        return str(default)

    def build_execution_trace(self, context: RequestContext):
        """
        Assemble the request-level entry point for Visitor traversal.

        The mediator is the right place to build this record because it already
        coordinates the full request lifecycle and has access to the records
        produced along the way.
        """
        from metis.inspection.records import ExecutionTrace, ResponseNode

        return ExecutionTrace(
            correlation_id=context.correlation_id,
            user_id=context.user_id,
            prompt_plan=self.build_prompt_plan_record(context),
            tool_commands=list(context.inspection_tool_commands),
            tool_results=list(context.inspection_tool_results),
            model_call=self.build_model_call_record(context),
            response=ResponseNode(
                content=(context.response or "")
                if self.config.get("inspection_include_content", False)
                else ""
            ),
        )

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
                    **exception_summary(exc),
                },
                metadata={"user_id": context.user_id},
                severity="ERROR",
            )
        )
