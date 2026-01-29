"""
WebTool for making HTTP requests asynchronously.
"""

import httpx
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse

from .base import BaseTool, ToolResult
from core.config import settings


class WebTool(BaseTool):
    """Tool for making HTTP requests."""

    name = "web"
    description = "Make HTTP requests to web services"

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
                    "url": {
                        "type": "string",
                        "description": "The URL to make the request to"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["get", "post"],
                        "description": "HTTP method to use"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to send in POST request (optional)"
                    }
                },
                "required": ["url", "method"]
            }
        }

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute HTTP request."""
        if action not in ["get", "post"]:
            return ToolResult(error=f"Unknown action: {action}")

        url = kwargs.get("url")
        if not url:
            return ToolResult(error="URL is required")

        try:
            host = ""
            try:
                host = (urlparse(url).hostname or "").lower()
            except Exception:
                host = ""

            trust_env = settings.HTTP_TRUST_ENV
            if host in {"localhost", "127.0.0.1"}:
                trust_env = False

            self.logger.info(f"WebTool request: action={action} url={url} host={host} trust_env={trust_env}")

            async with httpx.AsyncClient(timeout=30.0, trust_env=trust_env) as client:
                if action == "get":
                    response = await client.get(url)
                elif action == "post":
                    data = kwargs.get("data", {})
                    response = await client.post(url, json=data)

                response.raise_for_status()
                return ToolResult(output=response.text)

        except httpx.HTTPError as e:
            return ToolResult(error=f"HTTP error: {str(e)}")
        except Exception as e:
            return ToolResult(error=f"Request failed: {str(e)}")