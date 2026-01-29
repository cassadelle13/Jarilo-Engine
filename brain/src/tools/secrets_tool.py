"""
SecretsTool for accessing encrypted user secrets.
"""

from typing import Optional
import logging

from sqlalchemy import select

from orm.db import db_manager
from orm.models import Secret
from security.encryption import encryption_service

from .base import BaseTool, ToolResult


class SecretsTool(BaseTool):
    """Tool for accessing user secrets."""

    name = "secrets"
    description = "Access encrypted user secrets"

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
                    "action": {
                        "type": "string",
                        "enum": ["get"],
                        "description": "Action to perform"
                    },
                    "key": {
                        "type": "string",
                        "description": "The secret key to retrieve"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Optional user id scope for the secret (recommended)"
                    }
                },
                "required": ["action", "key"]
            }
        }

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute secrets operation."""
        if action != "get":
            return ToolResult(error=f"Unknown action: {action}")

        key = kwargs.get("key")
        if not key:
            return ToolResult(error="Key is required")

        user_id = kwargs.get("user_id")

        try:
            if not getattr(db_manager, "async_session_maker", None):
                return ToolResult(error="Database not initialized")

            async with db_manager.async_session_maker() as session:
                stmt = select(Secret).where(
                    Secret.key == key,
                    Secret.is_deleted == False,
                )
                if user_id:
                    stmt = stmt.where(Secret.user_id == user_id)
                result = await session.execute(stmt)
                secret = result.scalar_one_or_none()

                if not secret:
                    scope = f" for user_id={user_id}" if user_id else ""
                    return ToolResult(error=f"Secret not found for key '{key}'{scope}")

                try:
                    value = encryption_service.decrypt(secret.encrypted_value)
                except Exception as e:
                    return ToolResult(error=f"Failed to decrypt secret '{key}': {str(e)}")

                return ToolResult(output=value)

        except Exception as e:
            return ToolResult(error=f"Failed to access secret: {str(e)}")