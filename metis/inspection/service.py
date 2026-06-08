"""
Inspection service for running visitors over execution traces.

The service centralizes visitor execution so request handlers, tests, CLI tools,
and future support dashboards do not need to know traversal details.
"""

from __future__ import annotations

from .visitors import (
    LatencyVisitor,
    PromptInspectionVisitor,
    TokenUsageVisitor,
    TraceVisitor,
)


class InspectionService:
    """
    Small façade over Visitor execution.
    """

    def run(self, execution_trace, visitor):
        """
        Run any visitor over an execution trace and return the populated visitor.
        """
        execution_trace.accept(visitor)
        return visitor

    def trace(self, execution_trace):
        """Return a TraceVisitor populated from the given trace."""
        return self.run(execution_trace, TraceVisitor())

    def tokens(self, execution_trace, tokenizer=None):
        """Return a TokenUsageVisitor populated from the given trace."""
        return self.run(execution_trace, TokenUsageVisitor(tokenizer))

    def latency(self, execution_trace):
        """Return a LatencyVisitor populated from the given trace."""
        return self.run(execution_trace, LatencyVisitor())

    def prompt(self, execution_trace):
        """Return a PromptInspectionVisitor populated from the given trace."""
        return self.run(execution_trace, PromptInspectionVisitor())
