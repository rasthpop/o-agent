from typing import Any

from tools.base_tool import BaseTool


def create_tool_schema(tool: BaseTool) -> dict[str, Any]:
    """
    Converts a tool into Claude's expected schema format.

    Args:
        tool: The tool instance to convert

    Returns:
        A dictionary matching Claude's tool schema specification
    """
    return {
        "name": tool.get_name(),
        "description": tool.get_description(),
        "input_schema": tool.get_parameters(),
    }


def register_tools(tools: list[BaseTool]) -> tuple[list[dict], dict[str, BaseTool]]:
    """
    Registers multiple tools and creates lookup structures.

    Args:
        tools: List of tool instances to register

    Returns:
        A tuple of (tool_schemas, tool_map) for agent use
    """
    tool_schemas = [create_tool_schema(tool) for tool in tools]
    tool_map = {tool.get_name(): tool for tool in tools}

    return tool_schemas, tool_map
