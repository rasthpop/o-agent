"""Example: Detective agent using PlonkitSearchTool for geolocation."""

import logging

from anthropic import Anthropic
from anthropic.types import MessageParam, ToolResultBlockParam

from app.config import settings
from app.tools.plonkit_search.plonkit_search import PlonkitSearchTool
from app.tools.registry import register_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DETECTIVE_SYSTEM_PROMPT = """You are a detective agent specialized in geolocation investigations.

Your goal is to identify the location of images based on visual clues extracted from them.

You have access to the Plonkit database, which contains detailed information about:
- License plates and vehicle characteristics by country
- Road infrastructure (signs, markings, bollards, poles, guardrails)
- Vegetation, climate, and landscape patterns
- Architecture and building styles
- Language patterns and text clues
- Regional and city-specific identifiers

When given image features, use the plonkit_search tool to find matching countries:
1. Extract key searchable terms from the image features
2. Search for multiple related keywords at once
3. Analyze the results and identify the most likely locations
4. Provide confidence levels based on the number and specificity of matches

Always explain your reasoning and cite specific clues from the database."""


def run_detective_investigation(image_features: dict, metadata: dict):
    """Run a detective investigation using extracted image features.

    Args:
        image_features: Dict with textual_features and environment_features
        metadata: Image metadata (EXIF, etc.)
    """
    # Initialize Anthropic client
    client = Anthropic(api_key=settings.anthropic_api_key)

    # Initialize the Plonkit search tool
    plonkit_tool = PlonkitSearchTool()

    # Register tools for Claude API
    tool_schemas, tool_map = register_tools([plonkit_tool])

    # Prepare the investigation query
    user_message = f"""I need to identify the location of an image. Here are the extracted features:

TEXTUAL FEATURES:
{image_features.get("textual_features", "None extracted")}

ENVIRONMENT FEATURES:
{image_features.get("environment_features", "None extracted")}

IMAGE METADATA:
{metadata}

Please analyze these features and use the plonkit_search tool to identify the most likely location.
Search for relevant keywords and provide your top location guesses with confidence levels."""

    logger.info("Starting detective investigation...")
    logger.info(f"Image features: {image_features}")

    # Create initial message
    messages: list[MessageParam] = [{"role": "user", "content": user_message}]

    # Agentic loop - allow multiple tool calls
    max_iterations = 5
    for iteration in range(max_iterations):
        logger.info(f"Iteration {iteration + 1}")

        # Call Claude API
        response = client.messages.create(
            model=settings.default_model,
            max_tokens=4000,
            system=DETECTIVE_SYSTEM_PROMPT,
            tools=tool_schemas,
            messages=messages,
        )

        logger.info(f"Stop reason: {response.stop_reason}")

        # Add assistant response to messages
        messages.append({"role": "assistant", "content": response.content})

        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract final text response
            final_response = ""
            for block in response.content:
                if block.type == "text":
                    final_response += block.text

            logger.info("Investigation complete!")
            return final_response

        # Handle tool calls
        if response.stop_reason == "tool_use":
            tool_results: list[ToolResultBlockParam] = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    logger.info(f"Tool call: {tool_name}")
                    logger.info(f"Tool input: {tool_input}")

                    # Execute the tool
                    if tool_name in tool_map:
                        tool = tool_map[tool_name]
                        result = tool.execute(**tool_input)

                        logger.info(f"Tool result success: {result.success}")
                        if result.success:
                            logger.info(f"Found {result.data.get('total_matches', 0)} matches")

                        # Add tool result to messages
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result.data if result.success else result.error),
                            }
                        )

            # Add tool results as user message
            messages.append({"role": "user", "content": tool_results})

    return "Investigation reached maximum iterations without completion."


def example_investigation_1():
    """Example: Yellow license plate investigation."""
    print("=" * 80)
    print("EXAMPLE 1: Yellow License Plate Investigation")
    print("=" * 80)

    image_features = {
        "textual_features": {
            "visible_text": [],
            "language": "unknown",
            "signs": "No clear text visible on signs",
        },
        "environment_features": {
            "license_plates": "Yellow license plates visible on multiple vehicles",
            "road_markings": "White dashed center line, no outer lines visible",
            "landscape": "Flat terrain with sparse vegetation, desert-like",
            "architecture": "Low buildings, simple construction",
            "vehicle_types": "Pickup trucks common",
        },
    }

    metadata = {"gps_coordinates": None, "timestamp": "Unknown", "camera": "Unknown"}

    result = run_detective_investigation(image_features, metadata)
    print("\n" + "=" * 80)
    print("DETECTIVE FINDINGS:")
    print("=" * 80)
    print(result)


def example_investigation_2():
    """Example: Cyrillic text with specific architecture."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Cyrillic Text with Red Soil")
    print("=" * 80)

    image_features = {
        "textual_features": {
            "visible_text": ["Text in Cyrillic script on road signs"],
            "language": "Cyrillic",
            "signs": "Road signs with Cyrillic text",
        },
        "environment_features": {
            "license_plates": "White plates with some text",
            "road_markings": "White center line",
            "landscape": "Red/orange soil visible along roadside, moderately hilly",
            "vegetation": "Mixed forest and agricultural land",
            "architecture": "Mix of Soviet-era and modern buildings",
        },
    }

    metadata = {"gps_coordinates": None, "timestamp": "Summer", "camera": "Unknown"}

    result = run_detective_investigation(image_features, metadata)
    print("\n" + "=" * 80)
    print("DETECTIVE FINDINGS:")
    print("=" * 80)
    print(result)


if __name__ == "__main__":
    print("Starting Detective Agent Examples with Plonkit Database\n")

    # Run example investigations
    example_investigation_1()
    # example_investigation_2()  # Uncomment to run second example
