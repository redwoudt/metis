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

    # Cleaned input after DSL stripping
    clean_input: str = ""

    # Correlation ID for tracing/debugging
    correlation_id: str = field(default_factory=lambda: str(uuid4()))

    # DSL parsing output
    dsl_context: Dict[str, Any] = field(default_factory=dict)

    # Tool execution
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)

    # Session + engine
    session: Any = None
    engine: Any = None

    # Model selection
    model_role: str = "analysis"

    # Final response
    response: str = ""