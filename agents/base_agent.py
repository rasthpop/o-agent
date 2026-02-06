from typing import Any

import anthropic
from pydantic import BaseModel, Field

from config import settings
from tools.base_tool import BaseTool
from tools.registry import register_tools


class AgentMessage(BaseModel):
    """A message in the agent's conversation history."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgentResponse(BaseModel):
    """Response from an agent execution."""

    content: str = Field(..., description="The agent's response content")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, description="Tools called during execution"
    )
    stop_reason: str | None = Field(None, description="Reason the agent stopped")


class Agent:
    """
    An AI agent powered by Claude that can use tools to solve problems.
    """

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ):
        """
        Initialize the agent with tools and configuration.

        Args:
            tools: List of tool instances the agent can use
            model: Claude model identifier (defaults to settings.default_model)
            system_prompt: Custom system instructions for the agent
        """
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model or settings.default_model
        self.conversation_history: list[AgentMessage] = []

        # Set default system prompt if none provided
        self.system_prompt = system_prompt or settings.default_system_prompt

        # Register tools
        if tools:
            self.tool_schemas, self.tool_map = register_tools(tools)
        else:
            self.tool_schemas, self.tool_map = [], {}
