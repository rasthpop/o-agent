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
```

## Architecture

### Entry Point (`app/main.py`)

Current workflow (via `run_test_loop()`):
1. Extract features from image using vision API (text + environment analysis)
2. Initialize `InvestigationDB` with extracted features and metadata
3. Run `PlannerAgent.plan()` to generate investigation plan
4. Initialize `Detective` agent with tools (MainDBTool, WebSearchTool, WebScraperTool, OSMLookupTool, PlonkitSearchTool)
5. Execute `Detective.investigate_with_plan(plan)` - runs agentic loop until completion
6. Run `Summarizer.summarize(detective_response)` - extracts key findings with similarity check
7. Save summary to database if not redundant (similarity_score < 0.8)

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
- `summaries` - List of investigation summaries with key points (added by Summarizer)

Provides dict-like interface: `db["key"]`, `db.keys()`, `db.to_dict()`, etc.

### Agents (`app/agents/`)

**Base Agent Class** (`detective.py`):
- Foundation class for all agents with tool-calling capabilities
- Initialized with tools (BaseTool instances), model, and optional system_prompt
- Manages conversation history and tool registration via `register_tools()`
- Provides `tool_schemas` (Claude API format) and `tool_map` (name -> tool instance)

**PlannerAgent** (`planner.py`):
- Generates investigation plans based on current system state
- Two modes: initial planning (iteration 0) and refinement (iteration N)
- Uses prompts from `app/prompts/planner.py`
- Returns dict with `state` (context) and `next_steps` (ordered actions)

**Detective** (`detective.py`):
- Extends Agent class for executing structured investigation plans
- Core method: `investigate_with_plan(plan, max_iterations=25)`
- **Agentic Loop**: Iteratively calls Claude API with tools until plan completion
  - Extracts tool_use blocks from response
  - Executes tools via tool_map
  - Appends tool results to conversation
  - Continues until no tool calls or max_iterations reached
- Returns execution log with per-iteration tool calls, reasoning, and results
- Default tools: WebSearchTool, WebScraperTool, OSMLookupTool, PlonkitSearchTool, MainDBTool

**Summarizer** (`summarizer.py`):
- Extracts key findings from Detective execution logs
- Core method: `summarize(detective_response, check_similarity=True)`
- Produces structured output with: summary text, key_points (categorized findings), next_actions
- **Similarity Checking**: Compares new key points with existing summaries in database
  - Uses Claude to assess similarity (0.0-1.0 score)
  - Marks findings as redundant if similarity >= 0.8
  - Only saves non-redundant summaries to database
- Uses prompts from `app/prompts/summarizer.py`
- Key points include: category (location/evidence/hypothesis/contradiction), finding, confidence, source

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

**PlonkitSearchTool** (`app/tools/plonkit_search/`):
- Searches Plonkit geolocation database (`app/data/plonkit_full_database.json`)
- Database contains 200+ countries with detailed visual identification clues
- Search by keywords (license plates, road signs, vegetation, architecture, language)
- Returns matching countries with relevant sections and confidence scores
- Supports filtered search (limit to specific countries) and result limiting
- Usage: `tool.execute(keywords=["yellow plate", "cyrillic"], max_results=10)`

**WebSearchTool** (`web_search.py`):
- DuckDuckGo-powered web search via `ddgs` library
- Usage: `tool.execute(query="storefront matching [text]", max_results=5)`
- Returns formatted results with title, URL, and snippet

**WebScraperTool** (`web_scraper.py`):
- Extracts main text content from URLs using `trafilatura`
- Usage: `tool.execute(url="https://example.com")`
- Truncates output to 50,000 chars to prevent context overflow
- Handles bot protection and missing content gracefully

**OSMLookupTool** (`osm_search.py`):
- Queries OpenStreetMap Nominatim API for location coordinates
- Usage: `tool.execute(query="Eiffel Tower")`
- Returns display_name, latitude, longitude, and location type
- Includes custom User-Agent for Nominatim compliance

**MainDBTool** (`maindb_tool.py`):
- Read-only interface for agents to access InvestigationDB
- Actions: `get_state` (full snapshot), `get_field` (single field), `to_dict` (full dict)
- Usage: `tool.execute(action="get_field", field="initial_text")`
- Provides access to: initial_text, metadata, wrongs, context, history_of_validated_searches

### Prompts (`app/prompts/`)

Agents use prompts from this directory:
- `planner.py` - System prompts and user message templates for PlannerAgent
- `i2t.py` - Vision API prompts for text and environment extraction
- `summarizer.py` - Prompts for Summarizer agent (summarization and similarity checking)

## Code Quality

- Pre-commit hooks: **ruff** (lint/format)
- Ruff config: 100 char line length, Python 3.13 target
- All code must pass checks before commit
