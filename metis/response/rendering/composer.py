"""
Response Composer

Centralizes decorator ordering.

This prevents unpredictable layering bugs and keeps
rendering policy explicit.
"""

from typing import Any
from .component import BaseResponse, ResponseComponent
from .decorators import (
    SafetyDecorator,
    FormattingDecorator,
    CitationDecorator,
)


class ResponseComposer:
    """
    Applies decorators in deterministic order.

    Default order:
        1. Safety
        2. Formatting
        3. Citations
    """

    def compose(
        self,
        raw: str,
        preferences: dict[str, Any]
    ) -> ResponseComponent:
        """
        Apply decorators based on preference flags.
        """

        response: ResponseComponent = BaseResponse(raw)

        # NOTE:
        # Defaults are intentionally False to avoid
        # breaking existing state-based tests.

        if preferences.get("safety_enabled", False):
            response = SafetyDecorator(response)

        if preferences.get("format_markdown", False):
            response = FormattingDecorator(response)

        if preferences.get("include_citations", False):
            response = CitationDecorator(response)

        return response