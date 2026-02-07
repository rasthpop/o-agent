import base64
from PIL import Image, ImageEnhance
from app.tools.image_to_text.metadata import extract_image_metadata_for_agent

def load_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    

def resize_longest_side(img, target=1024):
    w, h = img.size
    scale = target / max(w, h)

    if scale >= 1:
        return img

    new_size = (int(w * scale), int(h * scale))
    return img.resize(new_size, Image.LANCZOS)

def preprocess_image(path):
    """Preprocess any image format for agent processing.

    Extracts metadata first (works with original HEIC/HEIF files),
    then converts to RGB JPEG for agent compatibility.

    Args:
        path: Path to the image file (supports JPEG, PNG, HEIC, HEIF, etc.)

    Returns:
        Tuple of (base64_string, metadata_dict, PIL_Image)
    """
    # Extract metadata before conversion (works with HEIC and all formats)
    metadata = extract_image_metadata_for_agent(path)

    # Open and convert image to RGB for agent processing
    img = Image.open(path)

    # Convert to RGB first (handles RGBA, P, L, CMYK, etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Apply enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)

    # Resize if needed
    img = resize_longest_side(img)

    # Save as JPEG for agent compatibility
    img.save((final_path := "app/images/preprocessed_image.jpg"), quality=95)
    base64_str = load_image_as_base64(final_path)

    return base64_str, metadata, img

if __name__ == "__main__":
    print(preprocess_image("app/images/col.HEIC")[1])