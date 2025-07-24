from metis.components.session_manager import SessionManager
from metis.components.tool_executor import ToolExecutor
from metis.prompts.builders.prompt_builder import PromptBuilder
from metis.policy.rate_limit import RateLimitPolicy
from metis.policy.auth import AuthPolicy
from metis.conversation_engine import ConversationEngine
from metis.memory.manager import MemoryManager
from metis.exceptions import ToolExecutionError
from metis.services.prompt_service import render_prompt  # NEW: imports new prompt logic

class RequestHandler:
    def __init__(self, strategy=None, policy=None, tool_executor=None, memory_manager=None):
        self.session_manager = SessionManager()
        self.tool_executor = tool_executor or ToolExecutor()
        self.prompt_builder = PromptBuilder()
        self.policy = policy or RateLimitPolicy()
        self.auth_policy = AuthPolicy()
        self.memory_manager = memory_manager or MemoryManager()

    def handle_prompt(self, user_id, user_input, save=False, undo=False):
        # Enforce user-level policies
        self.policy.enforce(user_id, user_input)
        self.auth_policy.enforce(user_id, user_input)

        # Load session and ensure engine is set
        session = self.session_manager.load_or_create(user_id)
        if not hasattr(session, "engine") or session.engine is None:
            session.engine = ConversationEngine()
        engine = session.engine

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

        # Determine if we should use the new prompt rendering system
        state = getattr(session, "state", "")
        if state in ["SummarizingState", "PlanningState", "ClarifyingState", "CritiqueState"]:
            # Use the new Builder + Template Method pattern
            prompt_text = render_prompt(
                prompt_type=state.replace("State", "").lower(),
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