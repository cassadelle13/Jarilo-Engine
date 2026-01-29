"""
DBTool for executing SQL queries asynchronously.
"""

from typing import Optional, List, Dict, Any
import logging

from .base import BaseTool, ToolResult


class DBTool(BaseTool):
    """Tool for executing read-only SQL queries."""

    name = "db"
    description = "Execute read-only SQL queries on the database"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (read-only)"
                    }
                },
                "required": ["query"]
            }
        }

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute SQL query."""
        if action != "query":
            return ToolResult(error=f"Unknown action: {action}")

        query = kwargs.get("query")
        if not query:
            return ToolResult(error="Query is required")

        # Check if it's a read-only query (basic check)
        query_upper = query.strip().upper()
        if not (query_upper.startswith("SELECT") or query_upper.startswith("SHOW") or query_upper.startswith("DESCRIBE")):
            return ToolResult(error="Only read-only queries are allowed (SELECT, SHOW, DESCRIBE)")

        try:
            # Import here to avoid circular imports
            from orm.db import get_db_session
            from sqlalchemy import text

            async for session in get_db_session():
                try:
                    result = await session.execute(text(query))
                    rows = result.fetchall()

                    # Convert to list of dicts
                    if rows:
                        columns = result.keys()
                        data = [dict(zip(columns, row)) for row in rows]
                        output = f"Found {len(data)} rows:\n"
                        for row in data[:10]:  # Limit to first 10 rows
                            output += str(row) + "\n"
                        if len(data) > 10:
                            output += f"... and {len(data) - 10} more rows"
                    else:
                        output = "Query executed successfully, no results returned."

                    return ToolResult(output=output)

                except Exception as e:
                    return ToolResult(error=f"Query execution failed: {str(e)}")
                finally:
                    await session.close()

        except Exception as e:
            return ToolResult(error=f"Database connection failed: {str(e)}")