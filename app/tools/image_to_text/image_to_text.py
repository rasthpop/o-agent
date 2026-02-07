import base64
import json
from anthropic import Anthropic
from app.config import settings
import app.tools.image_to_text.preprocessing as preprocessing

client = Anthropic(api_key=settings.anthropic_api_key)

# print(settings.anthropic_api_key)
# ---------- PROMPTS ----------

with open("app/tools/image_to_text/text_pass_prompt.txt", "r") as f:
    TEXT_PASS_PROMPT = f.read()
with open("app/tools/image_to_text/env_pass_prompt.txt", "r") as f:
    ENV_PASS_PROMPT = f.read()

# ---------- HELPER ----------

def _run_claude_vision(image_data, media_type, prompt):
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1200,
        temperature=0,  # reduces hallucination
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = response.content[0].text

    try:
        return json.loads(raw)
    except Exception:
        return {
            "parse_error": True,
            "raw_response": raw
        }


# ---------- MAIN FUNCTION ----------

def image_to_geoguessr_features(image_base64, media_type="image/jpeg"):
    """
    Performs two-pass multimodal feature extraction for GeoGuessr agent.

    Returns structured JSON with hallucination control.
    """

    # ----- PASS 1: TEXTUAL -----
    textual_features = _run_claude_vision(
        image_base64,
        media_type,
        TEXT_PASS_PROMPT
    )

    # ----- PASS 2: ENVIRONMENT -----
    environment_features = _run_claude_vision(
        image_base64,
        media_type,
        ENV_PASS_PROMPT
    )

    # ----- MERGE -----
    result = {
        "textual_features": textual_features,
        "environment_features": environment_features,
        "meta": {
            "extraction_warnings": []
        }
    }

    # Simple safety checks
    if "parse_error" in textual_features:
        result["meta"]["extraction_warnings"].append("Text pass JSON parse error")

    if "parse_error" in environment_features:
        result["meta"]["extraction_warnings"].append("Environment pass JSON parse error")

    return result


def load_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def final_run(path) -> tuple[dict, dict]:
    """
    Runs the full image to text pipeline and returns features along with the preprocessed image.
    """
    final_path, img = preprocessing.preprocess_image(path)


    image_base64 = load_image_as_base64(final_path)

    features = image_to_geoguessr_features(
        image_base64=image_base64,
        media_type="image/jpeg"
    )

    return features, img
