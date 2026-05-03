from typing import Any

from .context import RequestContext


class ConversationMediator:
    """
    Coordinates the full request lifecycle.

    NOTE: In PR1 this is a skeleton. Real logic will be added in PR2.
    """

    def __init__(
        self,
        session_manager: Any = None,
        dsl_interpreter: Any = None,
        model_factory: Any = None,
        event_bus: Any = None,
        services: Any = None,
    ):
        self.session_manager = session_manager
        self.dsl_interpreter = dsl_interpreter
        self.model_factory = model_factory
        self.event_bus = event_bus
        self.services = services

    # --- Public API ---

    def handle_request(self, user_id: str, user_input: str) -> str:
        """
        Entry point for handling a request.

        In PR1, this only prepares context and returns a placeholder.
        Full orchestration will be implemented in PR2.
        """
        context = self.prepare_context(user_id, user_input)

        # Placeholder behavior
        return f"[Mediator placeholder] Received: {context.user_input}"

    # --- Lifecycle steps (to be implemented in PR2) ---

    def prepare_context(self, user_id: str, user_input: str) -> RequestContext:
        context = RequestContext(
            user_id=user_id,
            user_input=user_input,
            clean_input=user_input,
        )
        return context

    def load_session(self, context: RequestContext) -> None:
        pass

    def parse_dsl(self, context: RequestContext) -> None:
        pass

    def select_model(self, context: RequestContext) -> None:
        pass

    def configure_engine(self, context: RequestContext) -> None:
        pass

    def execute_turn(self, context: RequestContext) -> None:
        pass

    def persist_session(self, context: RequestContext) -> None:
        pass