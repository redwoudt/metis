"""
Response Decorators

Each decorator modifies or enhances the output
without modifying the underlying generation logic.

This keeps generation and presentation independent.
"""

from .component import ResponseComponent


class ResponseDecorator(ResponseComponent):
    """
    Base decorator class.

    Holds a reference to another ResponseComponent.
    """

    def __init__(self, component: ResponseComponent):
        self._component = component

    def render(self) -> str:
        return self._component.render()


class SafetyDecorator(ResponseDecorator):
    """
    Placeholder for safety filtering.

    Currently a no-op to avoid test impact.
    """

    def render(self) -> str:
        content = super().render()
        # Integrate with moderation engine here later
        return content


class FormattingDecorator(ResponseDecorator):
    """
    Applies Markdown formatting wrapper.
    """

    def render(self) -> str:
        content = super().render()
        return f"## Response\n\n{content}"


class CitationDecorator(ResponseDecorator):
    """
    Appends source information.
    """

    def render(self) -> str:
        content = super().render()
        return f"{content}\n\nSources: [Model Generated]"