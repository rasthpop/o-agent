from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool
from tools.registry import register_tools
import os
import anthropic

class Agent:
    """
    An AI agent powered by Claude that can use tools to solve problems.
    """
    
    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        model: str = "claude-sonnet-4-20250514",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the agent with tools and configuration.
        
        Args:
            tools: List of tool instances the agent can use
            model: Claude model identifier
            system_prompt: Custom system instructions for the agent
        """
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Set default system prompt if none provided
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Register tools
        if tools:
            self.tool_schemas, self.tool_map = register_tools(tools)
        else:
            self.tool_schemas, self.tool_map = [], {}
    
    def _get_default_system_prompt(self) -> str:
        """Returns the default system prompt for the agent"""
        return """You are a helpful AI assistant that solves problems systematically.
        
When faced with complex questions, break them down into smaller steps.
Use available tools when you need to retrieve information or perform actions.
Think through problems logically and explain your reasoning.
Always verify your answers before presenting them to the user."""