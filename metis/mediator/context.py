from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class RequestContext:
    """
    Carries all state for a single request through the mediator pipeline.
    """

    user_id: str
    user_input: str

    clean_input: str = ""
    save: bool = False
    undo: bool = False

    correlation_id: str = field(default_factory=lambda: str(uuid4()))

    services: Any = None
    event_bus: Any = None

    dsl_context: Dict[str, Any] = field(default_factory=dict)

    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)

    # Visitor inspection records collected during the request lifecycle.
    # These are visitor-safe summaries, not references to private component internals.
    inspection_tool_commands: list[Any] = field(default_factory=list)
    inspection_tool_results: list[Any] = field(default_factory=list)

    # Request-level trace assembled by the mediator after execution completes.
    # Visitors enter through this object to inspect the completed request.
    execution_trace: Any = None

    session: Any = None
    engine: Any = None

    model_role: str = "analysis"
    model_client: Any = None
    model_manager: Any = None
    initial_state: Any = None

    response: str = ""
