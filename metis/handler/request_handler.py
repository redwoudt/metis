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
from config import Config
from metis.models.model_factory import ModelFactory
import re

# Initialize shared model factory using registry from config
model_factory = ModelFactory(Config.MODEL_REGISTRY)

class RequestHandler:
    def __init__(
        self,
        strategy=None,
        policy=None,
        tool_executor=None,
        memory_manager=None
    ):
        self.session_manager = SessionManager()
        self.tool_executor = tool_executor or ToolExecutor()
        self.prompt_builder = PromptBuilder()
        self.policy = policy or RateLimitPolicy()
        self.auth_policy = AuthPolicy()
        self.memory_manager = memory_manager or MemoryManager()

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        session = self.session_manager.load_or_create(user_id)
        if not hasattr(session, "engine") or session.engine is None:
            session.engine = ConversationEngine()
        engine = session.engine

        # DSL Parsing and session enrichment
        dsl_ctx = {}
        try:
            dsl_blocks = re.findall(r"\[[^\[\]:]+:[^\[\]]+?\]", user_input or "")
            if dsl_blocks:
                dsl_text = "".join(dsl_blocks)
                dsl_ctx = interpret_prompt_dsl(dsl_text)
                user_input = re.sub(r"\[[^\[\]:]+:[^\[\]]+?\]", "", user_input).strip()
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
                    merged_ctx = (existing_ctx + ("\n" if existing_ctx else "") + "\n".join(extras)).strip()
                    setattr(session, "context", merged_ctx)
        except Exception:
            dsl_ctx = {}

        # Undo or save snapshot
        if undo:
            snapshot = self.memory_manager.restore_last()
            if snapshot:
                engine.restore_snapshot(snapshot)
        elif save:
            snapshot = engine.create_snapshot()
            self.memory_manager.save(snapshot)

        # Tool execution enrichment
        if "weather" in user_input.lower():
            try:
                weather_data = self.tool_executor.execute("weather", user_input)
                user_input += f"\n(Weather Info: {weather_data})"
            except Exception as e:
                raise ToolExecutionError(str(e))

        # Determine state from DSL or session
        state = getattr(session, "state", "") or ""
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

        # Use role-based model selection via Factory → Singleton → Proxy
        model_role = dsl_ctx.get("task", "analysis").lower()
        try:
            selected_model = model_factory.get_model(model_role)
            setattr(session, "selected_model", selected_model)
            if hasattr(engine, "set_model") and callable(getattr(engine, "set_model")):
                engine.set_model(selected_model)
            else:
                setattr(engine, "model", selected_model)
        except Exception:
            pass  # Fallback to default engine setup

        if state in ["SummarizingState", "PlanningState", "ClarifyingState", "CritiqueState"]:
            state_to_prompt_type = {
                "SummarizingState": "summarize",
                "PlanningState": "plan",
                "ClarifyingState": "clarify",
                "CritiqueState": "critique",
            }
            prompt_type = state_to_prompt_type.get(state, state.replace("State", "").lower())
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
            prompt = self.prompt_builder.build(session, user_input)
            response = engine.respond(prompt)

        self.session_manager.save(user_id, session)
        return response