"""Plonkit database search tool for geolocation investigations."""

import json
import logging
import re
from pathlib import Path
from typing import Any

from app.tools.base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class PlonkitSearchTool(BaseTool):
    """Tool for searching the Plonkit geolocation database.

    Allows searching for countries and regions based on visual clues like:
    - License plate descriptions
    - Road signs and markings
    - Vegetation and climate features
    - Architecture styles
    - Bollards and poles
    - Language clues
    """

    def __init__(self, db_path: str | None = None):
        """Initialize Plonkit search tool.

        Args:
            db_path: Path to plonkit_full_database.json.
                    Defaults to app/data/plonkit_full_database.json
        """
        if db_path is None:
            # Default path relative to project root
            base_path = Path(__file__).parent.parent.parent / "data"
            self.db_path = base_path / "plonkit_full_database.json"
        else:
            self.db_path = Path(db_path)

        self.database = self._load_database()
        logger.info(f"Loaded Plonkit database with {len(self.database)} entries")

    def _load_database(self) -> list[dict[str, Any]]:
        """Load the Plonkit database from JSON file.

        Returns:
            List of country entries from the database.

        Raises:
            FileNotFoundError: If database file doesn't exist.
            json.JSONDecodeError: If database file is invalid JSON.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Plonkit database not found at {self.db_path}")

        with open(self.db_path, encoding="utf-8") as f:
            data: list[dict[str, Any]] = json.load(f)
            return data

    def get_name(self) -> str:
        """Returns the tool name."""
        return "plonkit_search"

    def get_description(self) -> str:
        """Returns what the tool does."""
        return """Search the Plonkit geolocation database for country identification clues.

This database contains detailed information about visual clues from around the world:
- License plates and vehicle characteristics
- Road signs, markings, and infrastructure (bollards, poles, guardrails)
- Vegetation, climate, and landscape features
- Architecture and building styles
- Language and text patterns
- Regional and city-specific identifiers

Use this tool when you have extracted visual features from an image and need to match
them against known country patterns. You can search for multiple keywords at once."""

    def get_parameters(self) -> dict[str, Any]:
        """Returns the parameter schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": """List of keywords to search for in the database.
Examples: ["yellow license plate", "cyrillic", "red soil", "wooden poles"].
The tool will search across all country descriptions for matches.""",
                    "minItems": 1,
                },
                "country_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": """Optional list of country names or codes to filter results.
If provided, only these countries will be searched. Useful for narrowing down search.""",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of country results to return. Defaults to 10.",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                },
            },
            "required": ["keywords"],
        }

    def _search_country(
        self,
        country: dict[str, Any],
        keywords: list[str],
        keyword_patterns: list[re.Pattern],
    ) -> dict[str, Any] | None:
        """Search a single country entry for keyword matches.

        Args:
            country: Country entry from database.
            keywords: List of keywords to search for.
            keyword_patterns: Pre-compiled regex patterns for keywords.

        Returns:
            Dict with country info and matching sections, or None if no matches.
        """
        matching_sections = []

        for section in country.get("sections", []):
            description = section.get("description", "")
            title = section.get("title", "")

            # Check if any keyword matches in this section
            matches = []
            for kw, pattern in zip(keywords, keyword_patterns):
                if pattern.search(description) or pattern.search(title):
                    matches.append(kw)

            if matches:
                matching_sections.append(
                    {
                        "title": title,
                        "description": description,
                        "matched_keywords": matches,
                    }
                )

        if matching_sections:
            return {
                "country": country["country"],
                "code": country["code"],
                "match_count": len(matching_sections),
                "matched_keywords": list(
                    set(kw for section in matching_sections for kw in section["matched_keywords"])
                ),
                "sections": matching_sections,
            }

        return None

    def execute(self, **kwargs) -> ToolResult:
        """Execute the Plonkit database search.

        Args:
            keywords: List of keywords to search for.
            country_filter: Optional list of countries to filter by.
            max_results: Maximum number of results to return (default 10).

        Returns:
            ToolResult with matching countries and their relevant sections.
        """
        try:
            keywords = kwargs.get("keywords", [])
            country_filter = kwargs.get("country_filter")
            max_results = kwargs.get("max_results", 10)

            if not keywords:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No keywords provided for search",
                    metadata={},
                )

            logger.info(f"Searching Plonkit database for keywords: {keywords}")

            # Compile regex patterns once for efficiency
            keyword_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]

            # Filter database if country filter provided
            search_database = self.database
            if country_filter:
                country_filter_lower = [c.lower() for c in country_filter]
                search_database = [
                    country
                    for country in self.database
                    if country["country"].lower() in country_filter_lower
                    or country["code"].lower() in country_filter_lower
                ]
                logger.info(f"Filtered to {len(search_database)} countries")

            # Search each country
            results = []
            for country in search_database:
                match_result = self._search_country(country, keywords, keyword_patterns)
                if match_result:
                    results.append(match_result)

            # Sort by number of matches (descending) and limit results
            results.sort(key=lambda x: x["match_count"], reverse=True)
            results = results[:max_results]

            logger.info(f"Found {len(results)} matching countries")

            return ToolResult(
                success=True,
                data={
                    "total_matches": len(results),
                    "keywords_searched": keywords,
                    "results": results,
                },
                error=None,
                metadata={
                    "database_size": len(self.database),
                    "countries_searched": len(search_database),
                },
            )

        except Exception as e:
            logger.error(f"Error searching Plonkit database: {e}", exc_info=True)
            return ToolResult(success=False, data=None, error=str(e), metadata={})
