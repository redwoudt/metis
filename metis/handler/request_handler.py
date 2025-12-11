import re
import logging

from metis.components.session_manager import SessionManager
from metis.prompts.builders.prompt_builder import PromptBuilder
from metis.policy.rate_limit import RateLimitPolicy
from metis.policy.auth import AuthPolicy
from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager
from metis.exceptions import ToolExecutionError
from metis.services.prompt_service import render_prompt
from metis.dsl import interpret_prompt_dsl
from metis.config import Config

from metis.models.model_factory import ModelFactory
from metis.components.model_manager import ModelManager

from metis.commands import command_registry
from metis.commands.base import ToolContext
from metis.handlers.pipelines import build_light_pipeline, build_strict_pipeline


logger = logging.getLogger(__name__)


class RequestHandler:
    """
    RequestHandler orchestrates both conversational reasoning and
    tool execution using Commands and the Chain of Responsibility.
    """

    def __init__(
        self,
        strategy=None,
        policy=None,
        memory_manager=None,
        config=None,
    ):
        self.session_manager = SessionManager()
        self.prompt_builder = PromptBuilder()
        self.policy = policy or RateLimitPolicy()
        self.auth_policy = AuthPolicy()
        self.memory_manager = memory_manager or MemoryManager()
        self.strategy = strategy

        self.config = config or {
            "vendor": getattr(Config, "DEFAULT_VENDOR", "openai"),
            "model": getattr(Config, "DEFAULT_MODEL", "gpt-4o-mini"),
            "policies": getattr(Config, "MODEL_POLICIES", {}),
        }

    # ----------------------------------------------------------------------
    # Tool execution entry point using Commands + Handler Pipeline
    # ----------------------------------------------------------------------
    def execute_tool(self, tool_name, args, user, services):
        """Execute a tool using the Command and Chain-of-Responsibility pipeline."""

        if tool_name not in command_registry:
            raise ToolExecutionError(f"Unknown tool '{tool_name}'")

        CommandCls = command_registry[tool_name]
        command = CommandCls()

        context = ToolContext(
            command=command,
            args=args,
            user=user,
            metadata={"allow_user_tools": True},
        )

        # Sensitive tools get stricter handlers
        if tool_name in {"execute_sql", "schedule_task"}:
            pipeline = build_strict_pipeline(services.quota, services.audit_logger)
        else:
            pipeline = build_light_pipeline()

        final_context = pipeline.handle(context)
        return final_context.result

    # ----------------------------------------------------------------------
    # Main request handling and conversation state machine
    # ----------------------------------------------------------------------
    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        logger.info(f"[handle_prompt] Called for user_id='{user_id}' with input='{user_input}'")

        # Policy enforcement
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        # Load session
        session = self.session_manager.load_or_create(user_id)
        engine = getattr(session, "engine", None)

        # Ensure engine has preferences dictionary
        if engine is not None and not hasattr(engine, "preferences"):
            engine.preferences = {}

        # ------------------------------------------------------------------
        # DSL parsing
        # ------------------------------------------------------------------
        dsl_ctx = {}
        try:
            dsl_blocks = re.findall(r"\[[^\[\]:]+:[^\[\]]+?\]", user_input or "")
            if dsl_blocks:
                dsl_text = "".join(dsl_blocks)
                dsl_ctx = interpret_prompt_dsl(dsl_text)

                # Remove DSL tags from visible user input
                user_input = re.sub(r"\[[^\[\]:]+:[^\[\]]+?\]", "", user_input).strip()

                # Update persona, tone, context, etc.
                if dsl_ctx.get("persona"):
                    setattr(session, "persona", dsl_ctx["persona"])
                if dsl_ctx.get("tone"):
                    setattr(session, "tone", dsl_ctx["tone"])

                extras = []
                if dsl_ctx.get("source"):
                    extras.append(f"Source: {dsl_ctx['source']}")
                if dsl_ctx.get("length"):
                    extras.append(f"Length: {dsl_ctx['length']}")
                if dsl_ctx.get("format"):
                    extras.append(f"Format: {dsl_ctx['format']}")

                if extras:
                    existing = getattr(session, "context", "")
                    merged = (
                        existing
                        + ("\n" if existing else "")
                        + "\n".join(extras)
                    ).strip()
                    setattr(session, "context", merged)

        except Exception as exc:
            logger.exception("[RequestHandler] DSL parse error: %s", exc)
            dsl_ctx = {}

        # ------------------------------------------------------------------
        # Undo / Save snapshot (Memento pattern)
        # ------------------------------------------------------------------
        if undo:
            snapshot = self.memory_manager.restore_last()
            if snapshot and engine is not None:
                engine.restore_snapshot(snapshot)
        elif save:
            if engine is not None:
                snapshot = engine.create_snapshot()
                self.memory_manager.save(snapshot)

        # ------------------------------------------------------------------
        # Tool selection (from DSL or future model tool calls)
        # ------------------------------------------------------------------
        tool_name = None
        tool_args = {}

        # DSL-driven tool selection
        if "tool" in dsl_ctx:
            tool_name = dsl_ctx["tool"]
            tool_args = dsl_ctx.get("args", {})

        # Future extension: model-provided tool call structure
        if "tool_call" in dsl_ctx:
            tc = dsl_ctx["tool_call"]
            tool_name = tc.get("name")
            tool_args = tc.get("arguments", {})

        # Store tool information for ExecutingState
        if engine is not None and tool_name:
            if not hasattr(engine, "preferences"):
                engine.preferences = {}
            engine.preferences["tool_name"] = tool_name
            engine.preferences["tool_args"] = tool_args
            logger.info(f"[RequestHandler] Tool selected: {tool_name} {tool_args}")

        # ------------------------------------------------------------------
        # State resolution
        # ------------------------------------------------------------------
        state = getattr(session, "state", "") or ""

        if not state:
            if dsl_ctx.get("task"):
                mapping = {
                    "summarize": "SummarizingState",
                    "summary": "SummarizingState",
                    "plan": "PlanningState",
                    "planning": "PlanningState",
                    "clarify": "ClarifyingState",
                    "translate": "ClarifyingState",
                    "critique": "CritiqueState",
                    "review": "CritiqueState",
                }
                task = dsl_ctx["task"].strip().lower()
                state = mapping.get(task, "")

            elif self.strategy:
                state = self.strategy.determine_state_name(user_input, dsl_ctx)
                if state:
                    setattr(session, "state", state)

        # ------------------------------------------------------------------
        # Determine model role
        # ------------------------------------------------------------------
        if dsl_ctx.get("task"):
            model_role = dsl_ctx["task"].strip().lower()
        elif isinstance(state, str) and state:
            model_role = state.replace("State", "").lower()
        else:
            model_role = "analysis"

        # ------------------------------------------------------------------
        # Setup model manager
        # ------------------------------------------------------------------
        model_client = ModelFactory.for_role(model_role, self.config)
        model_manager = ModelManager(model_client)

        if engine is None:
            engine = ConversationEngine(model_manager=model_manager)
            session.engine = engine
            engine.preferences = {}
        else:
            engine.set_model_manager(model_manager)

        # ------------------------------------------------------------------
        # Prompt building and model response
        # ------------------------------------------------------------------
        known_states = [
            "SummarizingState",
            "ClarifyingState",
            "GreetingState",
            "ExecutingState",
        ]

        if state in known_states:
            type_map = {
                "SummarizingState": "summarize",
                "ClarifyingState": "clarify",
                "GreetingState": "greeting",
                "ExecutingState": "executing",
            }
            prompt_type = type_map.get(state, state.replace("State", "").lower())

            prompt_obj = render_prompt(
                prompt_type=prompt_type,
                user_input=user_input,
                context=getattr(session, "context", ""),
                tool_output=getattr(engine.preferences, "tool_output", ""),
                tone=getattr(session, "tone", ""),
                persona=getattr(session, "persona", ""),
            )

            prompt_text = (
                prompt_obj.render()
                if hasattr(prompt_obj, "render")
                else str(prompt_obj)
            )
            response = engine.respond(prompt_text)
        else:
            prompt_text = self.prompt_builder.build(session, user_input)
            response = engine.respond(prompt_text)

        # ------------------------------------------------------------------
        # Save session and return
        # ------------------------------------------------------------------
        self.session_manager.save(user_id, session)
        return response