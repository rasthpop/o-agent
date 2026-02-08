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

Multi-agent OSINT (Open Source Intelligence) system for geolocation investigations. Extracts features from images using Claude's vision API, plans investigation strategies, and collects intelligence from various sources. Currently focused on GeoGuessr-style location identification.

## Setup Commands

```bash
# Install dependencies and sync environment
uv sync

# Install Playwright browsers (required for web scraping)
uv run playwright install

# Install pre-commit hooks
uv run pre-commit install

# Configure environment - create .env file with:
# ANTHROPIC_API_KEY=your_key_here
```

## Development Commands

```bash
# Run application
uv run python -m app.main

# Run pre-commit hooks manually
uv run pre-commit run --all-files

# Run specific checks
uv run ruff check .
uv run ruff format .
uv run mypy .
```

## Architecture

### Entry Point (`app/main.py`)

Current workflow:
1. Extract features from image using vision API (text + environment analysis)
2. Initialize `InvestigationDB` with extracted features and metadata
3. Run `PlannerAgent` to generate investigation plan
4. Plan contains `state` (context) and `next_steps` (list of actions)

### Configuration (`app/config.py`)

Uses **Pydantic Settings** for environment-based config:
- `settings.anthropic_api_key` - Anthropic API key
- `settings.default_model` - Default Claude model (claude-sonnet-4-20250514)
- `settings.default_system_prompt` - Default agent system prompt
- `create_anthropic_client()` - Factory function for creating Anthropic clients

### Investigation Database (`app/data/maindb.py`)

`InvestigationDB` - Dict-like database storing investigation state:
- `initial_photo` - Path to starting image
- `initial_text` - Extracted features from vision API
- `metadata` - Image metadata (EXIF, etc.)
- `wrongs` - User corrections for incorrect guesses
- `context` - User-provided contextual hints
- `history_of_validated_searches` - Validated search results

Provides dict-like interface: `db["key"]`, `db.keys()`, `db.to_dict()`, etc.

### Agents (`app/agents/`)

**PlannerAgent** (`planner.py`):
- Generates investigation plans based on current system state
- Two modes: initial planning (iteration 0) and refinement (iteration N)
- Uses prompts from `app/prompts/planner.py`
- Returns dict with `state` and `next_steps`

**Base Agent Pattern** (`detective.py` is the template):
- Agents receive `Anthropic` client, `InvestigationDB`, and model name
- Use specialized prompts for their domain
- Parse Claude responses into structured JSON using `extract_json_from_response()`

### Image Processing (`app/tools/image_to_text/`)

**Two-pass vision extraction:**
1. `TEXT_PASS_PROMPT` - Extract text, signs, labels (hallucination-controlled)
2. `ENV_PASS_PROMPT` - Extract environment features (climate, architecture, vegetation)

**Pipeline** (`image_to_text.py`):
- `extract_json_description_and_metadata(path)` - Full pipeline entry point
- `preprocessing.preprocess_image()` - Handles HEIF/HEIC conversion, EXIF extraction
- Uses Claude Opus 4.6 for vision API calls

### Utilities

**JSON Extraction** (`app/utils/claude_to_json.py`):
- `extract_json_from_response()` - Parses JSON from Claude responses (handles markdown fences)

**HTML Downloader** (`app/utils/download_html.py`):
- Playwright-based scraper for Plonkit country data
- Includes anti-bot measures (random delays, user agent rotation)
- Supports resumable downloads (skips existing files)

### Tool System

**BaseTool** (`app/tools/base_tool.py`):
- Abstract base for tools
- Methods: `get_name()`, `get_description()`, `get_parameters()`, `execute()`
- Returns `ToolResult` with: `success`, `data`, `error`, `metadata`

**Tool Registry** (`app/tools/registry.py`):
- `create_tool_schema()` - Converts BaseTool to Claude API tool schema
- `register_tools()` - Batch registration returning (schemas, tool_map)

### Prompts (`app/prompts/`)

Agents use prompts from this directory:
- `planner.py` - System prompts and user message templates for PlannerAgent
- `i2t.py` - Vision API prompts for text and environment extraction

## Code Quality

- Pre-commit hooks: **ruff** (lint/format) + **mypy** (type check)
- Ruff config: 100 char line length, Python 3.13 target
- Mypy: `--ignore-missing-imports` enabled for external dependencies
- All code must pass checks before commit
