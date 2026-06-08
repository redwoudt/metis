"""
Visitor-based inspection package for Mêtis.

This package implements Chapter 13's Visitor Pattern example: immutable runtime
records provide traversal, while focused visitors provide instrumentation.
"""

from .records import (
    BaseVisitor,
    ExecutionTrace,
    ModelCallRecord,
    PromptPlan,
    PromptSection,
    ResponseNode,
    ToolCommandRecord,
    ToolResultRecord,
    Visitable,
    Visitor,
)
from .service import InspectionService
from .visitors import (
    LatencyVisitor,
    PromptInspectionVisitor,
    SimpleTokenizer,
    TokenUsageVisitor,
    TraceVisitor,
)

__all__ = [
    "BaseVisitor",
    "ExecutionTrace",
    "InspectionService",
    "LatencyVisitor",
    "ModelCallRecord",
    "PromptInspectionVisitor",
    "PromptPlan",
    "PromptSection",
    "ResponseNode",
    "SimpleTokenizer",
    "TokenUsageVisitor",
    "ToolCommandRecord",
    "ToolResultRecord",
    "TraceVisitor",
    "Visitable",
    "Visitor",
]
