
import json
import re
from typing import Any, Dict
import logging
logger = logging.getLogger(__name__)

def extract_json_from_response(response_text: str) -> Dict[str, Any]:
        """Extract JSON object from Claude's response text.

        Args:
            response_text: Raw response text from Claude.

        Returns:
            Parsed JSON dict.
        """
        # Try to find JSON object in the response
        # Look for content between triple backticks first
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find a JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                logger.error("Could not find JSON in response: %s", response_text[:200])
                raise ValueError("No JSON found in response")

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON: %s", str(e))
            logger.error("JSON string: %s", json_str[:500])
            raise