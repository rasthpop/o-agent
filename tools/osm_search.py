import requests
from typing import Any
from .base_tool import BaseTool, ToolResult

class OSMLookupTool(BaseTool):
    """
    Tool to query OpenStreetMap (Nominatim).
    """

    def get_name(self) -> str:
        return "lookup_location"

    def get_description(self) -> str:
        return "Get coordinates and address details for a location name. Use this to verify if a landmark exists in a specific city."

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The location name, address, or landmark to look up (e.g. 'Eiffel Tower', 'Baker Street, London')"
                }
            },
            "required": ["query"]
        }

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        url = "https://nominatim.openstreetmap.org/search"
        # Nominatim requires a unique User-Agent
        headers = {'User-Agent': 'O-Agent-GeoDetective/1.0'}
        params = {'q': query, 'format': 'json', 'limit': 3}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return ToolResult(success=True, data="No location found in OpenStreetMap database.")
            
            results = []
            for item in data:
                name = item.get('display_name', 'Unknown')
                lat = item.get('lat')
                lon = item.get('lon')
                type_ = item.get('type', 'location')
                results.append(f"Found: {name}\nCoordinates: {lat}, {lon} ({type_})")
                
            return ToolResult(success=True, data="\n---\n".join(results))
        except Exception as e:
            return ToolResult(success=False, error=str(e))