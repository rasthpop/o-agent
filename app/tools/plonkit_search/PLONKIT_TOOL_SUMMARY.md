# Plonkit Search Tool - Implementation Summary

## Overview

I've created a complete search tool that allows the detective agent to query the Plonkit geolocation database (`plonkit_full_database.json`). The tool follows the BaseTool pattern and integrates seamlessly with Claude's tool-use API.

## What Was Created

### 1. Core Tool Implementation
- **`app/tools/plonkit_search/plonkit_search.py`** - Main tool class
- **`app/tools/plonkit_search/__init__.py`** - Package exports

### 2. Documentation & Examples
- **`app/tools/plonkit_search/README.md`** - Complete usage documentation
- **`app/tools/plonkit_search/example_usage.py`** - Standalone tool examples
- **`app/examples/detective_with_plonkit.py`** - Full detective agent integration

### 3. Updated Documentation
- **`CLAUDE.md`** - Added PlonkitSearchTool to architecture section

## Features

### Search Capabilities
✅ **Keyword Search** - Search by visual features (e.g., "yellow license plate", "cyrillic", "red soil")
✅ **Multi-feature Search** - Combine multiple keywords for better accuracy
✅ **Country Filtering** - Narrow search to specific countries
✅ **Result Limiting** - Control number of results (1-50, default 10)
✅ **Confidence Scoring** - Results ranked by number of matching sections

### Tool Parameters

```python
{
    "keywords": ["yellow plate", "wooden poles"],  # Required
    "country_filter": ["Argentina", "Brazil"],     # Optional
    "max_results": 10                              # Optional (1-50)
}
```

### Return Format

```python
{
    "success": True,
    "data": {
        "total_matches": 5,
        "keywords_searched": ["yellow license plate"],
        "results": [
            {
                "country": "Alaska",
                "code": "US-AK",
                "match_count": 1,
                "matched_keywords": ["yellow license plate"],
                "sections": [...]
            }
        ]
    },
    "metadata": {
        "database_size": 200,
        "countries_searched": 200
    }
}
```

## Quick Start

### 1. Test the Tool Directly

```bash
# Run standalone examples
uv run python -m app.tools.plonkit_search.example_usage
```

**Output:**
```
Found 7 countries
Denmark (DK)
  Matched keywords: ['yellow plate']
India (IN)
  Matched keywords: ['yellow plate']
...
```

### 2. Use with Detective Agent

```python
from anthropic import Anthropic
from app.config import settings
from app.tools.plonkit_search import PlonkitSearchTool
from app.tools.registry import register_tools

# Initialize
client = Anthropic(api_key=settings.anthropic_api_key)
plonkit_tool = PlonkitSearchTool()

# Register for Claude API
tool_schemas, tool_map = register_tools([plonkit_tool])

# Use in conversation
response = client.messages.create(
    model=settings.default_model,
    max_tokens=4000,
    tools=tool_schemas,
    messages=[{
        "role": "user",
        "content": "Find countries with yellow license plates and cyrillic text"
    }]
)

# Handle tool calls
for block in response.content:
    if block.type == "tool_use":
        tool = tool_map[block.name]
        result = tool.execute(**block.input)
```

### 3. Run Full Detective Agent Example

```bash
# Run complete investigation example
uv run python -m app.examples.detective_with_plonkit
```

This demonstrates a full agentic loop where the detective:
1. Receives image features
2. Calls plonkit_search with relevant keywords
3. Analyzes results
4. Provides location guesses with confidence levels

## Integration with Your Architecture

The tool fits into your iterative investigation process:

```
1. Input → Image + text context
2. Img2Text → Extract features (text + environment)
3. Planner → Determine search goals
4. Detective → 🆕 Use PlonkitSearchTool to search database
5. Validator → Decide relevance
6. Guesser → Make top 5 location guesses
7. User feedback → Continue if needed
```

## Example Searches

### Yellow License Plates
```python
tool.execute(keywords=["yellow license plate"])
# Returns: Denmark, India, Laos, Alaska, etc.
```

### Multi-Feature (Red Soil + Cyrillic)
```python
tool.execute(keywords=["red soil", "cyrillic"])
# Returns: Countries matching both features
```

### Architecture Search
```python
tool.execute(keywords=["orange tiled roofs", "pastel colours"])
# Returns: Albania, France, Argentina, etc.
```

### Regional Focus
```python
tool.execute(
    keywords=["red soil"],
    country_filter=["Argentina", "Brazil", "Chile"]
)
# Only searches South American countries
```

## Database Content

The Plonkit database contains detailed clues for 200+ countries/regions:
- **License plates** - Colors, formats, unique features
- **Road infrastructure** - Signs, markings, bollards, poles, guardrails
- **Landscape** - Vegetation, climate, terrain, soil colors
- **Architecture** - Building styles, roof types, materials
- **Language** - Scripts, common words (e.g., "rruga" = street in Albanian)
- **Regional clues** - City-specific landmarks, unique coverage types

## Next Steps

1. **Integrate with PlannerAgent** - Have planner suggest search keywords
2. **Add to ValidatorAgent** - Validate Plonkit results against other sources
3. **Create GuesserAgent** - Use Plonkit results to make location guesses
4. **Add Internet Search Tool** - Complement Plonkit with web searches
5. **Build Feedback Loop** - User corrections feed back to planner

## Testing

The tool has been tested and verified:
- ✅ Loads 200+ country database successfully
- ✅ Keyword search works across all sections
- ✅ Multi-keyword search combines results
- ✅ Country filtering narrows results
- ✅ Results properly ranked by relevance
- ✅ Integrates with Claude tool-use API

## Files Created

```
app/
├── tools/
│   └── plonkit_search/
│       ├── __init__.py              # Package exports
│       ├── plonkit_search.py        # Main tool (300 lines)
│       ├── README.md                # Usage documentation
│       └── example_usage.py         # Standalone examples
├── examples/
│   └── detective_with_plonkit.py    # Full agent integration (200 lines)
└── data/
    └── plonkit_full_database.json   # Database (already exists)

CLAUDE.md                             # Updated with tool info
PLONKIT_TOOL_SUMMARY.md              # This file
```

## Questions?

Check these resources:
- `app/tools/plonkit_search/README.md` - Detailed usage guide
- `app/tools/plonkit_search/example_usage.py` - Simple examples
- `app/examples/detective_with_plonkit.py` - Full agent integration
