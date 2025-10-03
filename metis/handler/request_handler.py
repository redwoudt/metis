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
from metis.models.model_factory import ModelFactory, ModelProxy
import re
import logging

logger = logging.getLogger(__name__)

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
        self.strategy = strategy
        self.model_factory = model_factory  # Expose factory for testing

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        logger.info(f"[handle_prompt] Called for user_id='{user_id}' with input='{user_input}'")
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        session = self.session_manager.load_or_create(user_id)
        logger.debug(f"[handle_prompt] Loaded session: {session}")
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
                logger.info(f"[handle_prompt] DSL context extracted: {dsl_ctx}")
                logger.debug(f"[handle_prompt] Cleaned user_input: {user_input}")
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

        # Determine state from session, DSL, or strategy
        state = getattr(session, "state", "") or ""
        logger.info(f"[handle_prompt] State from session: '{state}'")

        if not state:
            logger.info(f"[handle_prompt] State nothing from session: '{state}'")

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
                # Persist the resolved state into the session so subsequent calls see it
                if state:
                    setattr(session, "state", state)
                    logger.debug(f"[handle_prompt] Saved state '{state}' to session")

        logger.info(f"[handle_prompt] State determined: '{state}'")

        # Use role-based model selection via Factory → Singleton → Proxy
        # Map State class names like 'SummarizingState' -> role names used in the registry
        state_to_role = {
            "SummarizingState": "summarize",
            "ClarifyingState": "clarify",
            "GreetingState": "greeting",
            "ExecutingState": "executing",
        }
        # Determine model role
        if dsl_ctx.get("task"):
            model_role = dsl_ctx["task"].strip().lower()
        elif isinstance(state, str):
            model_role = state.replace("State", "").lower()
        elif hasattr(state, "__class__"):
            model_role = state.__class__.__name__.replace("State", "").lower()
        else:
            model_role = "analysis"
        logger.debug(
            f"[handle_prompt] Resolved model_role='{model_role}' (state='{state}', dsl_task='{dsl_ctx.get('task')}')")
        selected_model = model_factory.get_model(model_role)
        logger.debug(f"[handle_prompt] Selected model: {selected_model}")
        engine.set_model(selected_model)

        logger.info(f"[handle_prompt] Engine responding using state: {state or 'default'}")
        if state in ["SummarizingState", "ClarifyingState", "GreetingState", "ExecutingState"]:
            logger.debug(f"[handle_prompt] Engine responding using state: {state or 'default'} in special condition")

            state_to_prompt_type = {
                "SummarizingState": "summarize",
                "ClarifyingState": "clarify",
                "GreetingState": "greeting",
                "ExecutingState": "executing",
            }
            prompt_type = state_to_prompt_type.get(state, state.replace("State", "").lower()) if isinstance(state, str) else state.__class__.__name__.replace("State", "").lower()
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
            logger.debug(f"[handle_prompt] Engine responding using state: {state or 'default'} in prompt_builder")

            prompt = self.prompt_builder.build(session, user_input)
            response = engine.respond(prompt)

        logger.debug(f"[handle_prompt] Response: {response[:200]}")
        self.session_manager.save(user_id, session)
        return response