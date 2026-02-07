"""Configuration management using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from anthropic import Anthropic

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic API Configuration
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude access")

    # Agent Configuration
    default_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Default Claude model to use",
    )

    default_system_prompt: str = Field(
        default="""You are a helpful AI assistant that solves problems systematically.

When faced with complex questions, break them down into smaller steps.
Use available tools when you need to retrieve information or perform actions.
Think through problems logically and explain your reasoning.
Always verify your answers before presenting them to the user.""",
        description="Default system prompt for agents",
    )


# Global settings instance
settings = Settings()


def create_anthropic_client():
    """Factory function to create an Anthropic client using settings."""
    
    return Anthropic(api_key=settings.anthropic_api_key)