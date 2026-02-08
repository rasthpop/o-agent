# =============================================================================
# CATEGORY 0: TEXT 
# =============================================================================
TEXT_PASS_PROMPT = """
You are a forensic OCR and linguistic signal extraction system for geolocation.

STRICT RULES:
- Extract ONLY visible textual or language-based evidence.
- DO NOT infer country or region.
- If unsure → return null.
- Always include confidence integer, from values 0 to 5 where 0 is little to no confidence and 5 is really confident.
- Always quote observed evidence.

Return ONLY valid JSON.

Schema:

{
  "signage_text": [
    {"value": str, "confidence": int}
  ],
  "languages": [
    {"value": str, "confidence": int}
  ],
  "alphabets": [
    {"type": str, "confidence": int}
  ],
  "phone_numbers": [
    {"raw": str, "country_code_guess": str|null, "confidence": int}
  ],
  "domains": [
    {"value": str, "confidence": int}
  ],
  "license_plates": [
    {
      "color_pattern": str|null,
      "format_pattern": str|null,
      "confidence": int
    }
  ],
  "brand_names": [
    {"value": str, "confidence": int}
  ],
  "other_unidentified": [{"value": str}]
}
"""
# =============================================================================
# CATEGORY 1: PHYSICAL INFRASTRUCTURE & ENVIRONMENT
# =============================================================================
ENV_INFRASTRUCTURE_PROMPT = """
Analyze the image for visual geolocation clues. DO NOT extract any text. Focus only on physical attributes, colors, and shapes.
Output ONLY valid JSON. No markdown, no code fences. If a field is not observable, use "not visible".


Analyze the image for sun position, shadows, and sky clues to estimate hemisphere, latitude band, and camera heading.
DO NOT extract any text. Output ONLY valid JSON. No markdown, no code fences. If not determinable, use "unknown".


IF GEODATA IS GIVEN FROM IMAGE METADATAUSE THAT GEOLOCATION DATA INSTEAD!!!


Guidance:
- sun_altitude_estimate: near horizon ~5deg, moderate ~30deg, high ~60deg, near zenith ~80+deg
- shadow_length_vs_object_height: 2x=low sun ~27deg, 1x=~45deg, 0.5x=~63deg, none=zenith
- confidence: high/medium/low with brief reason


Guidance:
- car_type: sedan, pickup, SUV, blurred
- surface: asphalt, concrete, red soil, gravel, potholes
- line_colors_and_style: double yellow center, white dashed, no lines
- bollards: shape and color pattern
- pole_material_and_shape: wood/concrete/metal, round/square/ladder-style
- insulators: trident, horizontal bar, glass discs
- vegetation: tropical palms, pine, birch, dry scrub, grassland
- soil_color: red, orange, white sand, dark volcanic, grey
- driving_side: left-hand or right-hand traffic
Return ONLY this JSON:

{
  "camera_meta": {
    "car_color": "",
    "car_type": "",
    "antenna": "",
    "camera_quality": ""
  },
  "road": {
    "surface": "",
    "line_colors_and_style": "",
    "bollards": "",
    "guardrails": "",
    "sign_back_color_and_post_style": ""
  },
  "utilities": {
    "pole_material_and_shape": "",
    "insulators": "",
    "wiring_density": "",
    "street_light_type": ""
  },
  "landscape": {
    "vegetation": "",
    "soil_color": "",
    "terrain": "",
    "sky_and_weather": ""
  },
  "other_clues": {
    "notable_objects": "",
    "satellite_dish_direction": "",
    "driving_side": ""
  },
  "sun_and_shadows": {
    "sun_visible": "",
    "sun_position_in_frame": "",
    "sun_altitude_estimate": "",
    "shadow_direction_in_frame": "",
    "shadow_length_vs_object_height": ""
  },
  "sky_analysis": {
    "sky_gradient_description": "",
    "time_of_day_estimate": "",
    "moon_visible_and_phase": "",
    "stars_visible": ""
  } 
}





"""


# =============================================================================
# CATEGORY 2: ARCHITECTURE, CULTURE & REGION ESTIMATION
# =============================================================================
ENV_ARCHITECTURE_PROMPT = """
Analyze the image for architectural and cultural geolocation clues. DO NOT extract any text. Focus on physical attributes, colors, shapes, and styles.
Output ONLY valid JSON. No markdown, no code fences. If not visible, use "not visible".

Guidance:
- roof_material_and_shape: clay tiles+gable, corrugated metal+flat, slate+mansard, thatch, concrete flat with parapet
- wall_material_and_color: red brick, grey stone, concrete block, adobe, stucco with color, prefab panel, corrugated metal
- construction_completeness: rebar sticking up=Egypt/Lebanon/Turkey/LatAm, unfinished floors, fully complete
- roof_accessories: solar water heaters=Turkey/Greece/Israel, satellite dishes, TV antennas, chimney style
- plate_shape_and_colors: long rectangle vs short wide, white/yellow/blue strip. DO NOT read text.
- development_level: high/medium/low with brief description
- region_estimate: Provide country or sub-national level guesses. Require 3+ corroborating signals. State supporting evidence and conflicts.

Return ONLY this JSON:

{
  "buildings": {
    "roof_material_and_shape": "",
    "wall_material_and_color": "",
    "stories_and_density": "",
    "window_and_balcony_style": "",
    "construction_completeness": "",
    "roof_accessories": ""
  },
  "boundaries": {
    "fence_or_wall_type": "",
    "gate_style": ""
  },
  "religious_civic": {
    "worship_building_type": "",
    "civic_building_style": ""
  },
  "transport": {
    "plate_shape_and_colors": "",
    "dominant_vehicle_types": "",
    "public_transport": ""
  },
  "cultural": {
    "clothing_style": "",
    "street_commerce": "",
    "development_level": ""
  },
  "region_estimate": {
    "candidate_1_region": "",
    "candidate_1_evidence": "",
    "candidate_1_conflicts": "",
    "candidate_1_confidence": "",
    "candidate_2_region": "",
    "candidate_2_evidence": "",
    "candidate_2_confidence": "",
    "candidate_3_region": "",
    "candidate_3_evidence": "",
    "candidate_3_confidence": ""
  }
}

"""