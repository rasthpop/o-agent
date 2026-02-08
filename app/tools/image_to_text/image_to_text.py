
import app.tools.image_to_text.preprocessing as preprocessing
from app.tools.image_to_text.metadata import extract_image_metadata_for_agent
from app.utils.claude_to_json import extract_json_from_response

from app.config import settings, create_anthropic_client
from app.prompts.i2t import TEXT_PASS_PROMPT, ENV_ARCHITECTURE_PROMPT, ENV_INFRASTRUCTURE_PROMPT

client = create_anthropic_client()


def _run_claude_vision(image_data, media_type, prompt):
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1200,
        temperature=0,
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

    return extract_json_from_response(raw)



def image_to_geoguessr_features(image_base64, media_type="image/jpeg"):
    """
    Performs two-pass multimodal feature extraction for GeoGuessr agent.

    Returns structured JSON with hallucination control.
    """

    textual_features = _run_claude_vision(
        image_base64,
        media_type,
        TEXT_PASS_PROMPT
    )
    infrastructure_features = _run_claude_vision(
        image_base64,
        media_type,
        ENV_INFRASTRUCTURE_PROMPT
    )
    architecture_features = _run_claude_vision(
        image_base64,
        media_type,
        ENV_ARCHITECTURE_PROMPT
    )


    result = {
        "textual_features": textual_features,
        "architecture_features": architecture_features,
        "infrastructure_features": infrastructure_features,
        
        "meta": {
            "extraction_warnings": []
        }
    }


    return result




def extract_json_description_and_metadata(path) -> tuple[dict, dict]:
    """
    Runs the full image to text pipeline and returns features along with the preprocessed image.
    """
    image_base64, metadata, img = preprocessing.preprocess_image(path)

    features = image_to_geoguessr_features(
        image_base64=image_base64,
        media_type="image/jpeg"
    )

    return features, None, metadata


