"""
File system tools for Jarilo.
Adapted from Open-Interpreter's edit tool.
"""

import os
from pathlib import Path
from typing import Optional

from .base import BaseTool, ToolError, ToolResult


class FileTool(BaseTool):
    """Tool for file system operations."""

    name = "file_tool"
    description = "Tool for reading, writing, and managing files"

    def __init__(self):
        super().__init__()
        # Get workspace root from environment or use current directory
        self.workspace_root = os.getenv('JARILO_WORKSPACE_ROOT', os.getcwd())
        self.logger.info(f"FileTool initialized with workspace root: {self.workspace_root}")

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate file path within workspace."""
        # Convert to absolute path
        if not os.path.isabs(path):
            path = os.path.join(self.workspace_root, path)

        # Resolve any .. or . in path
        resolved_path = os.path.abspath(path)

        # Ensure path is within workspace
        if not resolved_path.startswith(self.workspace_root):
            raise ToolError(f"Access denied: path {resolved_path} is outside workspace {self.workspace_root}")

        return Path(resolved_path)

    async def read_file(self, path: str) -> ToolResult:
        """Read the content of a file."""
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return ToolResult(error=f"File {path} does not exist")

            content = file_path.read_text(encoding='utf-8')
            return ToolResult(output=content)

        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            return ToolResult(error=f"Error reading file: {str(e)}")

    async def write_file(self, path: str, content: str) -> ToolResult:
        """Write content to a file."""
        try:
            file_path = self._resolve_path(path)

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding='utf-8')
            return ToolResult(output=f"Successfully wrote to {path}")

        except Exception as e:
            self.logger.error(f"Error writing file {path}: {e}")
            return ToolResult(error=f"Error writing file: {str(e)}")

    async def append_file(self, path: str, content: str) -> ToolResult:
        """Append content to a file."""
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return ToolResult(error=f"File {path} does not exist")
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(output=f"Successfully appended to {path}")

        except Exception as e:
            self.logger.error(f"Error appending to file {path}: {e}")
            return ToolResult(error=f"Error appending to file: {str(e)}")

    async def list_directory(self, path: str = ".") -> ToolResult:
        """List contents of a directory."""
        try:
            dir_path = self._resolve_path(path)
            if not dir_path.exists():
                return ToolResult(error=f"Directory {path} does not exist")
            if not dir_path.is_dir():
                return ToolResult(error=f"Path {path} is not a directory")

            items = []
            for item in dir_path.iterdir():
                item_type = "dir" if item.is_dir() else "file"
                items.append(f"{item_type}: {item.name}")

            output = "\n".join(items) if items else "Directory is empty"
            return ToolResult(output=output)

        except Exception as e:
            self.logger.error(f"Error listing directory {path}: {e}")
            return ToolResult(error=f"Error listing directory: {str(e)}")

    async def create_directory(self, path: str) -> ToolResult:
        """Create a directory."""
        try:
            dir_path = self._resolve_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return ToolResult(output=f"Successfully created directory {path}")

        except Exception as e:
            self.logger.error(f"Error creating directory {path}: {e}")
            return ToolResult(error=f"Error creating directory: {str(e)}")

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute file operation based on action."""
        if action == "read":
            return await self.read_file(kwargs.get("path", ""))
        elif action == "write":
            return await self.write_file(kwargs.get("path", ""), kwargs.get("content", ""))
        elif action == "append":
            return await self.append_file(kwargs.get("path", ""), kwargs.get("content", ""))
        elif action == "list":
            return await self.list_directory(kwargs.get("path", "."))
        elif action == "mkdir":
            return await self.create_directory(kwargs.get("path", ""))
        else:
            return ToolResult(error=f"Unknown action: {action}")

    def get_schema(self) -> dict:
        """Get JSON schema for the tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "append", "list", "mkdir"],
                        "description": "Action to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write action)"
                    }
                },
                "required": ["action"]
            }
        }