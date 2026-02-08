# Plonkit Search Tool

A search tool for the detective agent to query the Plonkit geolocation database.

## Overview

The Plonkit database contains detailed visual clues for identifying countries and locations, including:
- License plates and vehicle characteristics
- Road infrastructure (signs, markings, bollards, poles)
- Vegetation and climate patterns
- Architecture styles
- Language patterns
- Regional identifiers

## Usage

### Basic Search

```python
from app.tools.plonkit_search import PlonkitSearchTool

tool = PlonkitSearchTool()
result = tool.execute(keywords=["yellow license plate"])

if result.success:
    for country in result.data["results"]:
        print(f"{country['country']}: {country['matched_keywords']}")
```

### Multi-Feature Search

```python
# Search for multiple features at once
result = tool.execute(
    keywords=["cyrillic", "red soil", "wooden poles"],
    max_results=5
)
```

### Filtered Search

```python
# Search only within specific countries
result = tool.execute(
    keywords=["red soil"],
    country_filter=["Argentina", "Brazil", "Chile"],
    max_results=5
)
```

## Integration with Detective Agent

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

# Use in messages.create()
response = client.messages.create(
    model=settings.default_model,
    max_tokens=4000,
    tools=tool_schemas,
    messages=[{"role": "user", "content": "Find countries with yellow plates"}]
)
```

## Tool Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keywords` | array[string] | Yes | Keywords to search for in descriptions |
| `country_filter` | array[string] | No | Filter to specific countries/codes |
| `max_results` | integer | No | Maximum results to return (1-50, default: 10) |

## Return Format

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
                "sections": [
                    {
                        "title": "Identifying Alaska",
                        "description": "...",
                        "matched_keywords": ["yellow license plate"]
                    }
                ]
            }
        ]
    },
    "metadata": {
        "database_size": 200,
        "countries_searched": 200
    }
}
```

## Examples

See `example_usage.py` for standalone examples and `app/examples/detective_with_plonkit.py` for full detective agent integration.

## Running Examples

```bash
# Basic tool usage examples
uv run python -m app.tools.plonkit_search.example_usage

# Full detective agent example
uv run python -m app.examples.detective_with_plonkit
```
