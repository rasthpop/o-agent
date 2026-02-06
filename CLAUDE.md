# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Guidelines

- Use Google docstrings
- Only create files that are explicitly requested or absolutely required
- Do not create example files, demo files, or test files unless specifically asked
- Avoid over-engineering - implement only what is requested, nothing more

## Git Rules

- Never use --force, only --force-with-lease

### Git Commit Rules

1. Separate subject from body with a blank line
2. Limit the subject line to 50 characters
3. Capitalize the subject line
4. Do not end the subject line with a period
5. Use the imperative mood in the subject line
6. Wrap the body at 72 characters
7. Use the body to explain what and why vs. how

## Project Overview

Multi-agent OSINT (Open Source Intelligence) system that autonomously plans investigations, collects intelligence from various sources, validates findings, and generates structured reports. Built using Claude API and LangGraph for agent orchestration.

## Setup Commands

```bash
# Install dependencies and sync environment
uv sync

# Install Playwright browsers (required for web scraping)
uv run playwright install

# Configure environment - create .env file with:
# ANTHROPIC_API_KEY=your_key_here
```

## Development Commands

```bash
# Run pre-commit hooks manually
uv run pre-commit run --all-files

# Run specific checks
uv run ruff check .
uv run ruff format .
uv run mypy .

# Run application
uv run python main.py
```

## Architecture

### Configuration Management (`config.py`)

Uses **Pydantic Settings** for type-safe configuration:
- All settings loaded from `.env` file via environment variables
- Access via global `settings` instance: `from config import settings`
- Key settings: `anthropic_api_key`, `default_model`, `default_system_prompt`
- Settings validated at startup with clear error messages

### Agent System (`agents/base_agent.py`)

**Base Agent Class:**
- Foundation for all specialized agents (Planner, Collector, Validator, Relation Builder, Reporter)
- Uses `settings.default_model` (Claude Sonnet 4 by default)
- Manages conversation history with Pydantic `AgentMessage` models
- Tool registration via registry system
- System prompts from `settings.default_system_prompt` or custom override

**Planned Specialized Agents** (empty placeholders):
1. `agents/planner.py` - Investigation planning
2. `agents/collector.py` - OSINT data collection
3. `agents/validator.py` - Fact validation
4. `agents/relation_builder.py` - Entity relationship mapping
5. `agents/reporter.py` - Report generation

### Tool System

**BaseTool** (`tools/base_tool.py`):
- Abstract base defining tool interface
- Methods: `get_name()`, `get_description()`, `get_parameters()`, `execute()`
- `execute()` returns `ToolResult` Pydantic model with: `success`, `data`, `error`, `metadata`

**Tool Registry** (`tools/registry.py`):
- `create_tool_schema()` - Converts BaseTool to Claude API schema
- `register_tools()` - Batch registration with lookup maps

### Key Patterns

**Creating New Agents:**
```python
from agents.base_agent import Agent
from config import settings

agent = Agent(
    tools=[tool1, tool2],
    system_prompt="Custom prompt for specialized agent"
)
```

**Creating New Tools:**
```python
from tools.base_tool import BaseTool, ToolResult

class MyTool(BaseTool):
    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data=result, metadata={})
```

**Using Settings:**
```python
from config import settings

# Access configuration
api_key = settings.anthropic_api_key
model = settings.default_model
```

## Code Quality

- Pre-commit hooks: **ruff** (lint/format) + **mypy** (type check)
- All code must pass checks before commit
- Run manually: `uv run pre-commit run --all-files`
