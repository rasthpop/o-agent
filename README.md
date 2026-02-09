# o-agent

An agentic GEOINT system that autonomously investigates images to determine their geographic location. Using Claude's vision API and an intelligent Detective agent, it extracts visual clues, plans investigation strategies, searches multiple data sources, and produces detailed location analyses.

## How It Works

The system uses a three-phase pipeline with a single autonomous agent:

1. **Planner** (LLM call) - Analyzes extracted image features and creates a structured investigation plan
2. **Detective Agent** - The autonomous agent that makes decisions and executes the plan using multiple GEOINT tools (web search, geographic databases, map services)
3. **Summarizer** (LLM call) - Extracts key findings, assigns confidence levels, and detects when investigation has converged

The Detective agent works in cycles, refining its understanding until it reaches a high-confidence location hypothesis or exhausts its investigation budget.

## Features

- **Autonomous Investigation**: Plans and executes multi-step GEOINT investigations without human intervention
- **Multi-Source Intelligence**: Searches PlonkIt geolocation database, web sources, OpenStreetMap, and specialized scrapers
- **Vision-Powered Feature Extraction**: Three-pass Claude vision analysis extracts text, signs, architecture, vegetation, and infrastructure details
- **Iterative Refinement**: The Detective agent cycles through planning and investigation phases, building on previous findings
- **Smart Convergence Detection**: Automatically stops when new findings become redundant
- **Structured Output**: Categorized findings: location, evidence, hypothesis, contradiction
- **Real-Time Web Interface**: Watch the agent work with live progress updates

## What It Can Identify

The system analyzes multiple types of visual clues:

- **Text & Signage**: Store names, street signs, license plates, advertisements
- **Architecture**: Building styles, construction materials, roof types
- **Infrastructure**: Road markings, utility poles, bollards, guardrails
- **Natural Features**: Vegetation types, climate indicators, terrain characteristics
- **Cultural Indicators**: Language patterns, regional design elements

## Installation

### For Users

1. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and setup**:
   ```bash
   git clone https://github.com/rasthpop/o-agent
   cd o-agent
   uv sync
   uv run playwright install
   ```

3. **Configure environment**:
   ```bash
   # Create .env file with:
   echo "ANTHROPIC_API_KEY=your_key_here" > .env
   ```

4. **Run**:
   ```bash
   # Web interface (recommended - opens on http://localhost:8000)
   uv run python -m app.web

   # CLI interface (for programmatic use)
   uv run python -m app.main
   ```

## Web Interface

The web interface provides a user-friendly way to run investigations:

1. **Start the server**:
   ```bash
   uv run python -m app.web
   ```

2. **Open your browser** to `http://localhost:8000`

3. **Upload an image** by dragging and dropping or clicking the upload area

4. **Watch the investigation progress** in real-time

5. **Review results** with categorized key findings

## For Developers

### Setup

1. Follow user installation steps above

2. Install pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

3. Run code quality checks:
   ```bash
   # Run all checks
   uv run pre-commit run --all-files

   # Or run individually
   uv run ruff check .
   uv run ruff format .
   ```

### Architecture Overview

The system is built around a single autonomous agent with supporting LLM calls:

- **Planner** (`app/agents/planner.py`) - LLM call that creates investigation plans based on extracted features and previous findings
- **Detective** (`app/agents/detective.py`) - The autonomous agent that makes decisions and executes plans using an agentic loop with tool-calling capabilities
- **Summarizer** (`app/agents/summarizer.py`) - LLM call that extracts key findings and checks for convergence

**Key Components**:
- `InvestigationDB` - Dict-like database storing all investigation state and history
- Tool system with `BaseTool` abstract class supporting: PlonkitSearch, WebSearch, WebScraper, OSMLookup, MainDB
- Three-pass vision extraction (text pass + environment pass)

## Troubleshooting

**"ModuleNotFoundError: No module named 'anthropic'"**
- Run `uv sync` to install dependencies

**"Playwright not installed" or browser errors**
- Run `uv run playwright install`

**"Missing ANTHROPIC_API_KEY"**
- Create a `.env` file in the project root with `ANTHROPIC_API_KEY=your_key_here`
- Get your API key from https://console.anthropic.com/

**Web interface not loading**
- Ensure you're accessing `http://localhost:8000` (not `https`)
- Check that port 8000 is not already in use

## Requirements

- Python 3.13+
- Anthropic API key ([Get one here](https://console.anthropic.com/))