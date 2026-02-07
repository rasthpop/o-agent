import trafilatura
from typing import Any
from .base_tool import BaseTool, ToolResult

class WebScraperTool(BaseTool):
    """
    Tool to extract main text from a URL.
    """

    def get_name(self) -> str:
        return "fetch_page"

    def get_description(self) -> str:
        return "Extract text content from a specific URL. Use this to read news articles or website 'About' pages to verify a location."

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to scrape (must start with http/https)"
                }
            },
            "required": ["url"]
        }

    def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded is None:
                return ToolResult(success=False, error="Could not retrieve page (bot protection or invalid URL).")
            
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if not text:
                return ToolResult(success=False, error="Page retrieved but no main text content found.")
            
            # Truncate to prevent context overflow
            return ToolResult(success=True, data=text[:50000])
        except Exception as e:
            return ToolResult(success=False, error=str(e))