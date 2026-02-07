from typing import Any

import anthropic
from config import settings
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool
from tools.registry import register_tools

import json
from typing import Dict, Any, List
# from .base_agent import Agent  # Importing your base Agent class
from app.tools.web_search import WebSearchTool
from app.tools.web_scraper import WebScraperTool
from app.tools.osm_search import OSMLookupTool


class AgentMessage(BaseModel):
    """A message in the agent's conversation history."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgentResponse(BaseModel):
    """Response from an agent execution."""

    content: str = Field(..., description="The agent's response content")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, description="Tools called during execution"
    )
    stop_reason: str | None = Field(None, description="Reason the agent stopped")


class Agent:
    """
    An AI agent powered by Claude that can use tools to solve problems.
    """

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ):
        """
        Initialize the agent with tools and configuration.

        Args:
            tools: List of tool instances the agent can use
            model: Claude model identifier (defaults to settings.default_model)
            system_prompt: Custom system instructions for the agent
        """
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model or settings.default_model
        self.conversation_history: list[AgentMessage] = []

        # Set default system prompt if none provided
        self.system_prompt = system_prompt or settings.default_system_prompt

        # Register tools
        if tools:
            self.tool_schemas, self.tool_map = register_tools(tools)
        else:
            self.tool_schemas, self.tool_map = [], {}

class Detective(Agent):
    """
    The Detective agent specifically tuned for Image-to-Text OSINT.
    """

    def __init__(self, tools=None, model=None):
        
        if model is None:
            model = settings.default_model

        if tools is None:
            tools = [WebSearchTool(), WebScraperTool(), OSMLookupTool()]

        self.tools = tools
            
        system_prompt = """
        You are the DETECTIVE, an elite OSINT investigator specializing in Geolocating images.
        
        YOUR INPUT:
        You will receive a structured 'Visual Intelligence Report' derived from an image.
        
        YOUR MISSION:
        Locate the location of the image. You must find the highest possible precision with the given data. The location can be as specific as a street address or as broad as a city, but the more precise, the better.
        
        STRATEGY:
        1. **Triangulate**: Combine text (Signage) + macro location (Flag/Language) + micro location (Businesses).
        2. **Resolve Conflicts**: Prioritize the physical evidence, supplied by the text. Use the macro indicators to narrow down the city/region, then use the micro indicators to find specific streets or landmarks.
        3. **Search Smart**:
           - Query 1: Search for the specific combination of visible brands.
           - Query 2: Search for unique architectural descriptions in the suspected city.
           - Query 3: Verify the address using the 'fetch_page' tool on the business website.
        4. **Map It**: Once you have a city and street, use 'lookup_location' to get coordinates.

        CRITICAL OPERATIONAL PROCEDURE:
        1. **SEARCH**: Start by searching for the text/landmarks visible in the image.
        2. **CAPTURE**: If search results return a specific website, IF AND ONLY IF it matches the visual evidence (e.g., storefront with matching brand), use 'fetch_page' to scrape the address from the business's website.
           - *DO NOT* perform another generic search if you have a specific URL to investigate.
           - *DO NOT* assume the address; read it from the page.
        3. **VERIFY**: Once you have scraped the address from the page, compare it against the visual evidence. Find closest matches to the data you have.
           - **IF** there are multiple leads, prioritize the one that matches the most features (e.g., correct brand + correct city).
        4. **LOCATE**: Only when you have a specific street address, use 'lookup_location' to get coordinates.
        
        Output format: Always conclude your turn with the next tool call or the final location.
        """
        super().__init__(tools=tools, model=model, system_prompt=system_prompt)

    def _format_feature_brief(self, data: Dict[str, Any]) -> str:
        """
        Parses the raw JSON to create a clean, high-signal briefing for the AI.
        Filters out low confidence (<0.6) and null values.
        """
        text_features = data.get("textual_features", {})
        env_features = data.get("environment_features", {})
        
        briefing = ["### VISUAL INTELLIGENCE REPORT ###\n"]

        # 1. TEXT & SIGNS (High Priority)
        signs = [t["value"] for t in text_features.get("signage_text", []) if t["confidence"] > 0.6]
        brands = [b["value"] for b in text_features.get("brand_names", []) if b["confidence"] > 0.8]
        if signs or brands:
            briefing.append("**DETECTED TEXT/BRANDS:**")
            if brands: briefing.append(f"- Brands: {', '.join(brands)}")
            if signs: briefing.append(f"- Signs: {', '.join(signs)}")

        # 2. MACRO LOCATION INDICATORS (Languages, Flags)
        langs = [l["value"] for l in text_features.get("languages", []) if l["confidence"] > 0.7]
        others = text_features.get("other_unidentified", []) + env_features.get("other_unidentified", [])
        flags = [item["value"] for item in others if "flag" in item["value"].lower()]
        
        if langs or flags:
            briefing.append("\n**LOCATION INDICATORS:**")
            if flags: briefing.append(f"- Visual Markers: {', '.join(flags)}")
            if langs: briefing.append(f"- Probable Language: {', '.join(langs)}")

        # 3. ENVIRONMENT & ARCHITECTURE
        arch = env_features.get("architecture", {})
        infra = env_features.get("infrastructure", {})
        
        if arch.get("confidence", 0) > 0.8 or infra.get("confidence", 0) > 0.8:
            briefing.append("\n**ENVIRONMENT:**")
            if arch.get("confidence", 0) > 0.8:
                briefing.append(f"- Architecture: {arch.get('roof_styles', '')}, {arch.get('building_materials', '')}")
            if infra.get("street_lights"):
                briefing.append(f"- Infrastructure: {infra['street_lights']}")

        return "\n".join(briefing)

    def investigate_image_features(self, image_data_json: Dict[str, Any]):
        """
        Entry point for the agent to start an investigation based on JSON data.
        """
        # 1. Convert JSON to Narrative
        intelligence_brief = self._format_feature_brief(image_data_json)
        
        print(f"--- GENERATED BRIEF ---\n{intelligence_brief}\n-----------------------")
        
        # 2. Inject into Agent Context
        # We wrap it in a user message to trigger the Agent's reasoning loop
        initial_message = (
            f"Here is the data extracted from the target image.\n"
            f"{intelligence_brief}\n\n"
            "Based on these features, start the search to find the location."
        )
        
        # 3. Start the loop (assuming your BaseAgent has a .run() or .chat() method)
        # Using the standard 'run' method from your context
        return self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": initial_message}],
                    tools=self.tool_schemas
                )