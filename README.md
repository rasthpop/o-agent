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
   # CLI interface
   uv run python -m app.main

   # Web interface (opens on http://localhost:8000)
   uv run python -m app.web
   ```

## Web Interface

The web interface provides a user-friendly way to run investigations:

1. **Start the server**:
   ```bash
   uv run python -m app.web
   ```

2. **Open your browser** to `http://localhost:8000`

3. **Upload an image** by dragging and dropping or clicking the upload area

4. **Watch the investigation progress** in real-time:
   - Image feature extraction
   - Investigation planning
   - Web searches and data collection
   - Analysis and summarization
   - Current investigation leads (e.g., "Currently considering Bosnia")

5. **Review results** with categorized key findings and confidence levels

### Features

- **Real-time Progress Updates**: Server-Sent Events stream progress as the investigation runs
- **Tool Usage Tracking**: See which tools are being used (web search, geolocation analysis, etc.)
- **Current Leads**: Shows the most promising location hypothesis during investigation
- **Structured Results**: Key findings organized by category (location, evidence, hypothesis, contradiction)
- **Confidence Scores**: Each finding includes a confidence level (high/medium/low)

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