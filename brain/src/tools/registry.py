"""
Tool registry for managing available tools in Jarilo.
"""

from typing import Dict, List, Type
import os
import json
import logging
from .base import BaseTool
from .file_tool import FileTool
from .shell_tool import ShellTool
from .web_tool import WebTool
from .db_tool import DBTool
from .secrets_tool import SecretsTool
from .auth_http_tool import AuthHttpTool
from .plugin_tool import PluginTool
from .code_generator_tool import CodeGeneratorTool


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tool instances."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {
            "file_tool": FileTool,
            "shell_tool": ShellTool,
            "web_tool": WebTool,
            "db_tool": DBTool,
            "secrets_tool": SecretsTool,
            "auth_http": AuthHttpTool,
            "code_generator_tool": CodeGeneratorTool,
        }
        self._plugin_tools: Dict[str, PluginTool] = {}
        self._initialize_tools()
        self._scan_plugins()

    def _initialize_tools(self):
        """Initialize all available tools."""
        for name, tool_class in self._tool_classes.items():
            try:
                self._tools[name] = tool_class()
            except Exception as e:
                logger.error(f"Failed to initialize tool {name}: {e}")

    def _scan_plugins(self):
        """Scan plugins directory and create virtual tools."""
        plugins_dir = "/app/plugins"
        if not os.path.exists(plugins_dir):
            logger.info("Plugins directory not found, skipping plugin scan")
            return

        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            manifest_path = os.path.join(plugin_path, "manifest.json")

            if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)

                    plugin_name = manifest["name"]
                    image_name = manifest.get("image_name")
                    logger.info(f"Loading plugin: {plugin_name}")

                    for tool_name, tool_config in manifest["tools"].items():
                        full_tool_name = f"{plugin_name}.{tool_name}"
                        self._plugin_tools[full_tool_name] = PluginTool(
                            plugin_name=plugin_name,
                            tool_name=tool_name,
                            description=tool_config["description"],
                            handler=tool_config["handler"],
                            plugin_path=plugin_path,
                            image_name=image_name
                        )
                        logger.info(f"Registered plugin tool: {full_tool_name}")

                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {e}")

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name."""
        if name in self._tools:
            return self._tools[name]
        elif name in self._plugin_tools:
            return self._plugin_tools[name]
        else:
            raise ValueError(f"Tool '{name}' not found")

    def get_all_tools(self) -> List[BaseTool]:
        """Get all available tools."""
        return list(self._tools.values()) + list(self._plugin_tools.values())

    def get_tool_names(self) -> List[str]:
        """Get names of all available tools."""
        return list(self._tools.keys()) + list(self._plugin_tools.keys())

    def get_tool_schemas(self) -> List[dict]:
        """Get JSON schemas for all tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute_tool(self, tool_name: str, action: str = None, **kwargs) -> dict:
        """Execute a tool action."""
        # Если tool_name содержит точку, парсим на tool и action
        if "." in tool_name:
            tool_base, action = tool_name.split(".", 1)
            # Map tool_base to actual tool name
            tool_mapping = {
                "file": "file_tool",
                "shell": "shell_tool",
                "web": "web_tool",
                "db": "db_tool",
                "secrets": "secrets_tool"
            }
            tool_base = tool_mapping.get(tool_base, tool_base)
            
            # Check if this is a plugin tool (full name)
            if tool_name in self._plugin_tools:
                tool = self.get_tool(tool_name)
                result = await tool.execute(action, **kwargs)
                return {
                    "tool": tool_name,
                    "action": action,
                    "success": result.error is None,
                    "output": result.output,
                    "error": result.error
                }
        else:
            tool_base = tool_name
        
        tool = self.get_tool(tool_base)
        
        result = await tool.execute(action, **kwargs)
        return {
            "tool": tool_name,
            "action": action,
            "success": result.error is None,
            "output": result.output,
            "error": result.error
        }


# Global registry instance
tool_registry = ToolRegistry()