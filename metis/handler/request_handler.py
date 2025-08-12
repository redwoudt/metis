from metis.components.session_manager import SessionManager
from metis.components.tool_executor import ToolExecutor
from metis.prompts.builders.prompt_builder import PromptBuilder
from metis.policy.rate_limit import RateLimitPolicy
from metis.policy.auth import AuthPolicy
from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager
from metis.exceptions import ToolExecutionError
from metis.services.prompt_service import render_prompt  # NEW: imports new prompt logic
from metis.handler.model_router import ModelRouter
from metis.dsl import interpret_prompt_dsl
import re

class RequestHandler:
    def __init__(
        self,
        strategy=None,
        policy=None,
        tool_executor=None,
        memory_manager=None,
        model_router: ModelRouter | None = None
    ):
        self.session_manager = SessionManager()
        self.tool_executor = tool_executor or ToolExecutor()
        self.prompt_builder = PromptBuilder()
        self.policy = policy or RateLimitPolicy()
        self.auth_policy = AuthPolicy()
        self.memory_manager = memory_manager or MemoryManager()
        self.model_router = model_router or ModelRouter()

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        # Enforce user-level policies
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        # Load session and ensure engine is set
        session = self.session_manager.load_or_create(user_id)
        if not hasattr(session, "engine") or session.engine is None:
            session.engine = ConversationEngine()
        engine = session.engine

        # --- DSL detection and merge (Interpreter pattern) ------------------------
        dsl_ctx = {}
        try:
            dsl_blocks = re.findall(r"\[[^\[\]:]+:[^\[\]]+?\]", user_input or "")
            if dsl_blocks:
                dsl_text = "".join(dsl_blocks)
                dsl_ctx = interpret_prompt_dsl(dsl_text)
                # Remove DSL blocks from the visible user_input before further processing
                user_input = re.sub(r"\[[^\[\]:]+:[^\[\]]+?\]", "", user_input).strip()
                # Persist persona/tone if provided
                if dsl_ctx.get("persona"):
                    setattr(session, "persona", dsl_ctx["persona"])
                if dsl_ctx.get("tone"):
                    setattr(session, "tone", dsl_ctx["tone"])
                # Merge extras into context so templates/builders can render them
                extras = []
                if dsl_ctx.get("source"):
                    extras.append(f"Source: {dsl_ctx['source']}")
                if dsl_ctx.get("length"):
                    extras.append(f"Length: {dsl_ctx['length']}")
                if dsl_ctx.get("format"):
                    extras.append(f"Format: {dsl_ctx['format']}")
                if extras:
                    existing_ctx = getattr(session, "context", "")
                    merged_ctx = (existing_ctx + ("\n" if existing_ctx else "") + "\n".join(extras)).strip()
                    setattr(session, "context", merged_ctx)
        except Exception:
            # Non-fatal: if DSL parse fails, continue with raw input
            dsl_ctx = {}
        # --------------------------------------------------------------------------

        # Undo or save snapshot
        if undo:
            snapshot = self.memory_manager.restore_last()
            if snapshot:
                engine.restore_snapshot(snapshot)
        elif save:
            snapshot = engine.create_snapshot()
            self.memory_manager.save(snapshot)

        # Optional: tool execution enrichment
        if "weather" in user_input.lower():
            try:
                weather_data = self.tool_executor.execute("weather", user_input)
                user_input += f"\n(Weather Info: {weather_data})"
            except Exception as e:
                raise ToolExecutionError(str(e))

        # Determine state, possibly from DSL task
        state = getattr(session, "state", "") or ""
        # Map DSL task → State class name if state not set
        if not state and dsl_ctx.get("task"):
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
            state = task_to_state.get(task_lc, state)

            # --- Model routing (select provider/model based on DSL/context) ---------
            try:
                selected_model = self.model_router.route(
                    ctx=dsl_ctx,
                    task=(dsl_ctx.get("task") if dsl_ctx else None),
                    persona=(dsl_ctx.get("persona") if dsl_ctx else None),
                    model=getattr(session, "preferred_model", None),
                )
                # Persist selection for observability and downstream use
                setattr(session, "selected_model", selected_model)
                # If the engine supports dynamic model configuration, apply it
                if hasattr(engine, "set_model") and callable(getattr(engine, "set_model")):
                    engine.set_model(selected_model)
                else:
                    # Fallback: store on engine for downstream consumers
                    setattr(engine, "model", selected_model)
            except Exception:
                # Non-fatal: fallback to engine defaults if routing fails
                pass
            # ------------------------------------------------------------------------

        if state in ["SummarizingState", "PlanningState", "ClarifyingState", "CritiqueState"]:
            # Map state classes to known template keys
            state_to_prompt_type = {
                "SummarizingState": "summarize",
                "PlanningState": "plan",
                "ClarifyingState": "clarify",
                "CritiqueState": "critique",
            }
            prompt_type = state_to_prompt_type.get(state, state.replace("State", "").lower())

            # Use the new Builder + Template Method pattern
            prompt_text = render_prompt(
                prompt_type=prompt_type,
                user_input=user_input,
                context=getattr(session, "context", ""),
                tool_output=getattr(session, "tool_output", ""),
                tone=getattr(session, "tone", ""),
                persona=getattr(session, "persona", "")
            )
            response = engine.respond(prompt_text)
        else:
            # Fallback to legacy prompt builder
            prompt = self.prompt_builder.build(session, user_input)
            response = engine.respond(prompt)

        # Save updated session state
        self.session_manager.save(user_id, session)

        return response