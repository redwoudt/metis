import re
import logging

from metis.components.session_manager import SessionManager
from metis.components.tool_executor import ToolExecutor
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
from metis.components.model_manager import ModelManager  # Bridge implementor

logger = logging.getLogger(__name__)


class RequestHandler:
    """
    RequestHandler is the orchestration entry point.

    - Gathers context (session, DSL, tool output).
    - Selects which "role" the model should play for this turn.
    - Builds the prompt.
    - Injects the right adapter (ModelClient) into the Bridge implementor (ModelManager),
      then into the ConversationEngine.
    - Asks the engine to respond.

    High-level flow / mental model:
        RequestHandler  -> ConversationEngine (state machine, Memento)
                         -> ModelManager (Bridge implementor)
                         -> Adapter (ModelClient for a vendor, via ModelFactory)

    The states inside ConversationEngine will call engine.generate_with_model(),
    so they never talk to Anthropic/OpenAI/etc. directly.
    """

    def __init__(
        self,
        strategy=None,
        policy=None,
        tool_executor=None,
        memory_manager=None,
        config=None,
    ):
        self.session_manager = SessionManager()
        self.tool_executor = tool_executor or ToolExecutor()
        self.prompt_builder = PromptBuilder()
        self.policy = policy or RateLimitPolicy()
        self.auth_policy = AuthPolicy()
        self.memory_manager = memory_manager or MemoryManager()
        self.strategy = strategy

        # Per-request / per-environment model config (which vendor, which model, etc.)
        # Falls back to global Config if not provided.
        self.config = config or {
            "vendor": getattr(Config, "DEFAULT_VENDOR", "openai"),
            "model": getattr(Config, "DEFAULT_MODEL", "gpt-4o-mini"),
            "policies": getattr(Config, "MODEL_POLICIES", {}),
        }

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        logger.info(
            f"[handle_prompt] Called for user_id='{user_id}' with input='{user_input}'"
        )

        # ---------------- Policy enforcement ----------------
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        # ---------------- Session load ----------------
        session = self.session_manager.load_or_create(user_id)
        logger.debug(f"[handle_prompt] Loaded session: {session}")

        # Attach engine placeholder if needed
        if not hasattr(session, "engine") or session.engine is None:
            session.engine = None
        engine = session.engine

        # ---------------- DSL parsing ----------------
        dsl_ctx = {}
        try:
            dsl_blocks = re.findall(r"\[[^\[\]:]+:[^\[\]]+?\]", user_input or "")
            if dsl_blocks:
                dsl_text = "".join(dsl_blocks)
                dsl_ctx = interpret_prompt_dsl(dsl_text)

                # Strip DSL hints from the visible user input
                user_input = re.sub(
                    r"\[[^\[\]:]+:[^\[\]]+?\]", "", user_input
                ).strip()

                logger.info(f"[handle_prompt] DSL context extracted: {dsl_ctx}")
                logger.debug(f"[handle_prompt] Cleaned user_input: {user_input}")

                # Persist tone/persona/context onto the session
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
                    existing_ctx = getattr(session, "context", "")
                    merged_ctx = (
                        existing_ctx
                        + ("\n" if existing_ctx else "")
                        + "\n".join(extras)
                    ).strip()
                    setattr(session, "context", merged_ctx)
        except Exception:
            # If DSL parsing explodes, we degrade gracefully and continue
            dsl_ctx = {}

        # ---------------- Snapshot / Undo (Memento) ----------------
        if undo:
            snapshot = self.memory_manager.restore_last()
            if snapshot and engine is not None:
                engine.restore_snapshot(snapshot)
        elif save:
            if engine is not None:
                snapshot = engine.create_snapshot()
                self.memory_manager.save(snapshot)

        # ---------------- Tool execution enrichment ----------------
        if "weather" in user_input.lower():
            try:
                weather_data = self.tool_executor.execute("weather", user_input)
                user_input += f"\n(Weather Info: {weather_data})"
            except Exception as e:
                raise ToolExecutionError(str(e))

        # ---------------- Determine conversation state ----------------
        state = getattr(session, "state", "") or ""
        logger.info(f"[handle_prompt] State from session: '{state}'")

        if not state:
            logger.info(
                "[handle_prompt] State not found in session, deriving..."
            )
            if dsl_ctx.get("task"):
                task_lc = dsl_ctx["task"].strip().lower()
                task_to_state = {
                    "summarize": "SummarizingState",
                    "summary": "SummarizingState",
                    "plan": "PlanningState",
                    "planning": "PlanningState",
                    "clarify": "ClarifyingState",
                    "translate": "ClarifyingState",
                    "critique": "CritiqueState",
                    "review": "CritiqueState",
                }
                state = task_to_state.get(task_lc, "")
                logger.info(f"[handle_prompt] State from task_lc: '{state}'")

            elif self.strategy:
                state = self.strategy.determine_state_name(user_input, dsl_ctx)
                logger.info(f"[handle_prompt] State from strategy: '{state}'")
                if state:
                    setattr(session, "state", state)
                    logger.debug(
                        f"[handle_prompt] Saved state '{state}' to session"
                    )

        logger.info(f"[handle_prompt] State determined: '{state}'")

        # ---------------- Map state/task to model role ----------------
        # Old world: model_factory.get_model(role)
        # New world: ModelFactory.for_role(role, config) -> ModelClient adapter
        if dsl_ctx.get("task"):
            model_role = dsl_ctx["task"].strip().lower()
        elif isinstance(state, str) and state:
            model_role = state.replace("State", "").lower()
        elif hasattr(state, "__class__"):
            model_role = state.__class__.__name__.replace(
                "State", ""
            ).lower()
        else:
            model_role = "analysis"

        logger.debug(
            f"[handle_prompt] Resolved model_role='{model_role}' "
            f"(state='{state}', dsl_task='{dsl_ctx.get('task')}')"
        )

        # Build a concrete adapter (Adapter pattern) for this role+config
        model_client = ModelFactory.for_role(model_role, self.config)

        # Bridge implementor: wraps the adapter so the engine stays provider-agnostic
        model_manager = ModelManager(model_client)

        # Ensure engine exists and is wired to the bridge implementor
        if engine is None:
            engine = ConversationEngine(model_manager=model_manager)
            session.engine = engine
        else:
            # If engine already exists, update its model_manager so routing decisions
            # can change across turns (summarizer vs planner, fallback vendor, etc.)
            if hasattr(engine, "set_model_manager"):
                engine.set_model_manager(model_manager)
            else:
                engine.model_manager = model_manager

        # ---------------- Build the actual prompt text ----------------
        logger.info(
            f"[handle_prompt] Engine responding using state: {state or 'default'}"
        )

        # Some states map directly to known prompt templates
        known_states = [
            "SummarizingState",
            "ClarifyingState",
            "GreetingState",
            "ExecutingState",
        ]

        if state in known_states:
            logger.debug(
                f"[handle_prompt] Using render_prompt path for state '{state or 'default'}'"
            )

            state_to_prompt_type = {
                "SummarizingState": "summarize",
                "ClarifyingState": "clarify",
                "GreetingState": "greeting",
                "ExecutingState": "executing",
            }

            prompt_type = state_to_prompt_type.get(
                state,
                state.replace("State", "").lower()
                if isinstance(state, str)
                else state.__class__.__name__.replace("State", "").lower(),
            )

            # Build a provider-agnostic prompt object
            prompt_obj = render_prompt(
                prompt_type=prompt_type,
                user_input=user_input,
                context=getattr(session, "context", ""),
                tool_output=getattr(session, "tool_output", ""),
                tone=getattr(session, "tone", ""),
                persona=getattr(session, "persona", ""),
            )

            # Normalize to string before handing to engine.respond(...)
            try:
                prompt_text = (
                    prompt_obj.render()
                    if hasattr(prompt_obj, "render")
                    else str(prompt_obj)
                )
            except Exception:
                prompt_text = str(prompt_obj)

            response = engine.respond(prompt_text)

        else:
            # Fallback path: use the generic prompt builder
            logger.debug(
                f"[handle_prompt] Using prompt_builder for state '{state or 'default'}'"
            )
            prompt_text = self.prompt_builder.build(session, user_input)
            response = engine.respond(prompt_text)

        # ---------------- Save session and return ----------------
        logger.debug(f"[handle_prompt] Response: {response[:200]}")
        self.session_manager.save(user_id, session)

        return response