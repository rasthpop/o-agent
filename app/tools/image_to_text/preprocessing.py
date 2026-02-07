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

    img = Image.open(path)
    metadata = extract_image_metadata_for_agent(path)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    img = resize_longest_side(img)
    img = img.convert("RGB")

    
    img.save((final_path := "app/images/preprocessed_image.jpg"), quality=95)
    base64_str = load_image_as_base64(final_path)
    return base64_str, metadata, img

if __name__ == "__main__":
    print(preprocess_image("app/images/col.jpg")[1])