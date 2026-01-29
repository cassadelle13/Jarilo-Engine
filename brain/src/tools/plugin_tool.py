"""
Plugin Tool - Virtual tool that executes commands in plugin containers.
"""

import os
import logging
from typing import Any, Dict
from .base import BaseTool, ToolResult
from .sandbox import PluginSandbox


class PluginTool(BaseTool):
    """
    Virtual tool that executes plugin commands in isolated containers.
    """

    def __init__(self, plugin_name: str, tool_name: str, description: str, handler: str, plugin_path: str, image_name: str = None):
        self.plugin_name = plugin_name
        self.tool_name = tool_name
        self.name = f"{plugin_name}.{tool_name}"
        self.description = description
        self.handler = handler
        self.plugin_path = plugin_path
        self.image_name = image_name or f"jarilo-plugin-{plugin_name}"
        super().__init__()

    async def execute(self, action: str = None, **kwargs) -> ToolResult:
        """
        Execute the plugin tool in a sandbox container.
        """
        try:
            # Create sandbox
            sandbox = PluginSandbox(self.plugin_path, image_name=self.image_name)

            # Start container
            await sandbox.start()

            # Prepare environment variables
            env_vars = {
                "TOOL_NAME": self.tool_name,
                "TOOL_ARGS": " ".join(str(v) for v in kwargs.values() if v is not None)
            }

            # Build command to run handler
            command = f"/{self.handler}"

            self.logger.info(f"Executing plugin command: {command}")
            self.logger.info(f"Handler: {self.handler}, type: {type(self.handler)}")
            self.logger.info(f"Plugin path: {self.plugin_path}")
            self.logger.info(f"Env vars: {env_vars}")

            # Execute and collect output
            output_lines = []
            async for line in sandbox.execute(command, env_vars):
                output_lines.append(line)
                self.logger.info(f"Plugin output: {line}")

            output = "\n".join(output_lines)

            # Stop container
            await sandbox.stop()

            return ToolResult(output=output)

        except Exception as e:
            self.logger.error(f"Plugin execution failed: {e}")
            self.logger.error(f"Exception type: {type(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return ToolResult(error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for the plugin tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application/project"
                    },
                    "template": {
                        "type": "string",
                        "description": "Template to use (e.g., react, vue)",
                        "default": "react"
                    }
                },
                "required": ["app_name"]
            }
        }