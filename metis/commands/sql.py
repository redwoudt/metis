from typing import Any
from .base import ToolCommand, ToolContext


class ExecuteSQLCommand(ToolCommand):
    name = "execute_sql"
    execution_policy = "strict"

    def execute(self, context: ToolContext) -> Any:
        statement = context.args.get("sql")
        if not statement:
            raise ValueError("Missing SQL statement.")

        # Replace with your actual SQL engine integration
        return {"status": "ok", "rows": []}
