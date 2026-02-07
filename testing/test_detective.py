import json
import os
from agents.detective import Detective

# --- 1. THE MOCK PLANNER INSTRUCTION ---
# Normally, the Planner would send this text. 
# We simulate it here as the "User Goal" the Detective is trying to solve.
PLANNER_INSTRUCTION = (
    "Investigation Goal: Geolocate the target based on the provided visual features. "
    "Prioritize finding the physical store location derived from the signage."
)

# --- 2. THE MOCK IMAGE DATA ---
IMAGE_DATA = {
  "textual_features": {
    "signage_text": [
      { "value": "NATURKOMPANIET", "confidence": 0.98 },
      { "value": "NATUR KOMPANIET", "confidence": 0.85 },
      { "value": "WAYNE", "confidence": 0.50 },
      { "value": "19", "confidence": 0.70 },
      { "value": "25", "confidence": 0.70 },
      { "value": "Søndag", "confidence": 0.55 }
    ],
    "languages": [
      { "value": "Swedish", "confidence": 0.80 },
      { "value": "Norwegian", "confidence": 0.75 }
    ],
    "alphabets": [
      { "type": "Latin", "confidence": 0.99 }
    ],
    "phone_numbers": [],
    "domains": [],
    "license_plates": [],
    "brand_names": [
      { "value": "Naturkompaniet", "confidence": 0.98 }
    ],
    "other_unidentified": [
      { "value": "Norwegian flag visible on building facade (red with blue and white cross)" },
      { "value": "A-frame sandwich board signs on sidewalk with partially legible text" },
      { "value": "No parking sign (circular red/blue) visible" }
    ]
  },

  "environment_features": {
    "environment": {
      "biome": "boreal/subarctic",
      "vegetation": "null",
      "terrain": "flat urban street",
      "urban_density": "medium-density town center",
      "confidence": 0.85
    },

    "road_features": {
      "lane_markings": "null",
      "pavement_type": "asphalt with snow/ice cover",
      "driving_side_hint": "null",
      "shoulder_style": "null",
      "confidence": 0.40
    },

    "infrastructure": {
      "bollards": "null",
      "utility_poles": "null",
      "guardrails": "null",
      "street_lights": "string lights/fairy lights strung across street",
      "sidewalks": "paved sidewalk along storefronts, snow-covered",
      "confidence": 0.75
    },

    "architecture": {
      "building_materials": "painted wooden clapboard/timber frame construction",
      "roof_styles": "steep gabled roofs with decorative wooden gable trim, pointed dormers, Nordic wooden vernacular style",
      "density": "continuous row of attached/semi-attached commercial buildings",
      "confidence": 0.95
    },

    "vehicles": {
      "brands": [],
      "taxi_patterns": "null",
      "confidence": 0.10
    },

    "astronomy": {
      "shadow_direction": "null",
      "sun_height": "very low sun angle, twilight/dusk conditions suggesting high latitude winter",
      "confidence": 0.80
    },

    "other_unidentified": [
      { "value": "Norwegian cross flag visible on building facade" },
      { "value": "heavy snow accumulation on rooftops and awnings" },
      { "value": "Christmas/holiday decorative lights on storefronts and strung overhead" },
      { "value": "traditional Scandinavian wooden architecture with green and cream paint colors" },
      { "value": "pedestrian shopping street or low-traffic commercial zone" },
      { "value": "A-frame sandwich board signs on sidewalk" },
      { "value": "no-stopping traffic sign (circular red border with blue center)" }
    ]
  }
}

def run_interactive_test():
    print("🕵️‍♂️ INITIALIZING DETECTIVE AGENT...")
    detective = Detective()
    
    # 1. PREPARE THE PROMPT
    # We access the internal helper to generate the same briefing the agent sees
    briefing = detective._format_feature_brief(IMAGE_DATA)
    
    initial_message = (
        f"Here is the data extracted from the target image.\n"
        f"{briefing}\n\n"
        "Based on these features, start the search to find the location."
    )

    # Initialize conversation history
    messages = [{"role": "user", "content": initial_message}]

    MAX_TURNS = 2
    turn_count = 0

    print(f"\n💬 USER PROMPT:\n{initial_message[:100]}...\n")

    # 2. START THE LOOP (With Safety Limit)
    while turn_count < MAX_TURNS:
        turn_count += 1
        print(f"\n🔄 TURN {turn_count}/{MAX_TURNS}")
        
        print("🤖 AGENT IS THINKING...")
        
        # Call Anthropic API with current history
        response = detective.client.messages.create(
            model=detective.model,
            max_tokens=4096,
            system=detective.system_prompt,
            messages=messages,
            tools=detective.tool_schemas
        )
        
        # Append the assistant's response to history (so it remembers what it said)
        messages.append({"role": "assistant", "content": response.content})
        
        # Print the text part of the response
        text_content = response.content[0].text if response.content else ""
        print(f"\n🗣️ AGENT: {text_content}")

        # 3. CHECK FOR TOOL USE
        if response.stop_reason == "tool_use":
            tool_results = []
            
            print("\n🛠️ EXECUTING TOOLS...")
            
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_args = block.input
                    tool_id = block.id
                    
                    print(f"  -> Calling: {tool_name}({tool_args})")
                    
                    # Find the matching tool in the detective's toolkit
                    # (The Detective class has a .tools list)
                    tool_instance = next((t for t in detective.tools if t.get_name() == tool_name), None)
                    
                    result_content = ""
                    if tool_instance:
                        # Execute the tool
                        try:
                            # Note: Your BaseTool might return a ToolResult object or string.
                            # We handle both for safety.
                            result = tool_instance.execute(**tool_args)
                            result_content = result.data if hasattr(result, 'data') else str(result)
                        except Exception as e:
                            result_content = f"Error executing tool: {e}"
                    else:
                        result_content = f"Error: Tool '{tool_name}' not found."

                    print(f"     [Result]: {str(result_content)[:100]}...")

                    # Add result to the list of tool outputs
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": str(result_content)
                    })
            
            # 4. FEED BACK TO AGENT
            # We must append the tool results as a user message (or specific tool_result block)
            messages.append({
                "role": "user",
                "content": tool_results
            })
            
            # Loop continues to next iteration (Agent reads result -> Thinks again)
            
        else:
            # If no tools are used, the agent is done (or asking a question)
            print("\n✅ AGENT FINISHED.")
            break

if __name__ == "__main__":
    run_interactive_test()