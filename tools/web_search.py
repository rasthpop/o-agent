from typing import Any
from duckduckgo_search import DDGS
from base_tool import BaseTool, ToolResult

class WebSearchTool(BaseTool):
    """
    Tool to search the web using DuckDuckGo.
    """
    
    def get_name(self) -> str:
        return "web_search"

    def get_description(self) -> str:
        return "Search the web for information. Use this to find addresses of businesses, cross-reference landmarks, or look up text found in images."

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'storefront matching [text]', 'landmark with blue dome in [city]')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)"
                }
            },
            "required": ["query"]
        }

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        max_results = kwargs.get("max_results", 5)
        
        try:
            results = []
            with DDGS() as ddgs:
                search_gen = ddgs.text(query, max_results=max_results)
                for r in search_gen:
                    results.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}")
            
            if not results:
                return ToolResult(success=True, data="No results found.")
                
            return ToolResult(success=True, data="\n---\n".join(results))
        except Exception as e:
            return ToolResult(success=False, error=str(e))