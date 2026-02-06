from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result from a tool execution."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    data: Any = Field(None, description="The result data from the tool")
    error: str | None = Field(None, description="Error message if execution failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the execution"
    )


class BaseTool:
    """Base class for all agent tools"""

    def get_name(self) -> str:
        """Returns the tool name"""
        raise NotImplementedError

    def get_description(self) -> str:
        """Returns what the tool does"""
        raise NotImplementedError

    def get_parameters(self) -> dict[str, Any]:
        """Returns the parameter schema for the tool"""
        raise NotImplementedError

    def execute(self, **kwargs) -> ToolResult:
        """Executes the tool with given parameters"""
        raise NotImplementedError
