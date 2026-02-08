# OSINT Agent

Multi-agent OSINT system that autonomously plans investigations, collects open-source intelligence, validates findings, and generates structured reports.

## Features

- Investigation planning agent
- Multi-source OSINT data collection
- Fact validation & correlation
- Explainable intelligence reporting

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
   uv run python -m app.main.py
   ```

### For Developers

1. **Follow user installation steps above**

2. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

3. **Run code quality checks**:
   ```bash
   # Run all checks
   uv run pre-commit run --all-files

   # Or run individually
   uv run ruff check .
   uv run ruff format .
   uv run mypy .
   ```

## Requirements

- Python 3.13+
- Anthropic API key