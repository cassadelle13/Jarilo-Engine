"""
Base classes for Jarilo tools system.
Adapted from Open-Interpreter's tool architecture.
"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any, Dict, Optional
import logging


@dataclass(kw_only=True, frozen=True)
class ToolResult:
    """Represents the result of a tool execution."""

    output: Optional[str] = None
    error: Optional[str] = None
    system: Optional[str] = None

    def __bool__(self):
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult"):
        def combine_fields(
            field: Optional[str], other_field: Optional[str], concatenate: bool = True
        ):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            system=combine_fields(self.system, other.system),
        )


class ToolError(Exception):
    """Exception raised by tools."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BaseTool(metaclass=ABCMeta):
    """Abstract base class for Jarilo tools."""

    name: str
    description: str

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for the tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }