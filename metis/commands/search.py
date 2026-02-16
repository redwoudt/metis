from typing import Any
from .base import ToolCommand, ToolContext


class SearchWebCommand(ToolCommand):
    name = "search_web"

    def execute(self, context: ToolContext) -> Any:
        query = context.args.get("query")
        if not query:
            raise ValueError("Missing 'query' argument for search_web.")

        # Replace with your actual search implementation
        return {"results": [f"Fake search result for '{query}'"]}