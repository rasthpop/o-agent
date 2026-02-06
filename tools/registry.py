from base_tool import BaseTool
from typing import Dict, Any, List

def create_tool_schema(tool: BaseTool) -> Dict[str, Any]:
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
        "input_schema": tool.get_parameters()
    }

def register_tools(tools: List[BaseTool]) -> tuple[List[Dict], Dict[str, BaseTool]]:
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