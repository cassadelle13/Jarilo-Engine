"""AuthHttpTool for making HTTP requests with credentials loaded from SecretsTool."""

from __future__ import annotations

import base64
import httpx
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from core.config import settings
from .base import BaseTool, ToolResult
from .secrets_tool import SecretsTool


class AuthHttpTool(BaseTool):
    name = "auth_http"
    description = "Make authenticated HTTP requests using credentials stored in secrets"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._secrets = SecretsTool()

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string", "enum": ["get", "post"]},
                    "body": {"type": ["object", "string", "null"]},
                    "headers": {"type": "object"},
                    "auth": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "enum": ["bearer", "basic", "api_key"]},
                            "credential_ref": {
                                "description": "Secret reference. Either string key or object {key, user_id}",
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "object",
                                        "properties": {
                                            "key": {"type": "string"},
                                            "user_id": {"type": "string"},
                                        },
                                        "required": ["key"],
                                    },
                                ],
                            },
                            "header_name": {"type": "string"},
                            "prefix": {"type": "string"},
                            "in": {"type": "string", "enum": ["header", "query"]},
                            "name": {"type": "string"},
                        },
                        "required": ["mode", "credential_ref"],
                    },
                },
                "required": ["url", "method", "auth"],
            },
        }

    async def execute(self, action: str, **kwargs) -> ToolResult:
        if action != "request":
            return ToolResult(error=f"Unknown action: {action}")

        url = kwargs.get("url")
        method = str(kwargs.get("method") or "get").lower()
        body = kwargs.get("body")
        headers = dict(kwargs.get("headers") or {})
        auth = kwargs.get("auth") or {}

        if not url:
            return ToolResult(error="url is required")
        if method not in {"get", "post"}:
            return ToolResult(error=f"Unsupported method: {method}")

        try:
            credential_ref = auth.get("credential_ref")
            secret_key: Optional[str] = None
            user_id: Optional[str] = None
            if isinstance(credential_ref, str):
                secret_key = credential_ref
            elif isinstance(credential_ref, dict):
                secret_key = credential_ref.get("key")
                user_id = credential_ref.get("user_id")

            if not secret_key:
                return ToolResult(error="auth.credential_ref is required")

            secret_result = await self._secrets.execute("get", key=secret_key, user_id=user_id)
            if secret_result.error:
                return ToolResult(error=secret_result.error)

            secret_value = str(secret_result.output or "")
            mode = str(auth.get("mode") or "").lower()

            if mode == "bearer":
                header_name = auth.get("header_name") or "Authorization"
                prefix = auth.get("prefix") or "Bearer "
                headers[header_name] = f"{prefix}{secret_value}".strip()

            elif mode == "basic":
                # By default expects secret in form username:password
                if ":" not in secret_value:
                    return ToolResult(error="basic auth secret must be in form 'username:password'")
                username, password = secret_value.split(":", 1)
                token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
                headers["Authorization"] = f"Basic {token}"

            elif mode == "api_key":
                placement = str(auth.get("in") or "header").lower()
                name = auth.get("name") or "X-API-Key"
                prefix = auth.get("prefix") or ""
                value = f"{prefix}{secret_value}".strip()

                if placement == "header":
                    headers[name] = value
                elif placement == "query":
                    sep = "&" if "?" in url else "?"
                    url = f"{url}{sep}{httpx.QueryParams({name: value})}"
                else:
                    return ToolResult(error=f"Unsupported api_key placement: {placement}")
            else:
                return ToolResult(error=f"Unsupported auth mode: {mode}")

            host = ""
            try:
                host = (urlparse(url).hostname or "").lower()
            except Exception:
                host = ""

            trust_env = settings.HTTP_TRUST_ENV
            if host in {"localhost", "127.0.0.1"}:
                trust_env = False

            self.logger.info(f"AuthHttpTool request: method={method} url={url} host={host} trust_env={trust_env}")

            async with httpx.AsyncClient(timeout=30.0, trust_env=trust_env) as client:
                if method == "get":
                    resp = await client.get(url, headers=headers)
                else:
                    resp = await client.post(url, headers=headers, json=body if body not in (None, "") else None)

                resp.raise_for_status()
                return ToolResult(output=resp.text)

        except httpx.HTTPError as e:
            return ToolResult(error=f"HTTP error: {str(e)}")
        except Exception as e:
            return ToolResult(error=f"Request failed: {str(e)}")
