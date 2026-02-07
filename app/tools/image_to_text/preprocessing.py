from PIL import Image, ImageEnhance


def resize_longest_side(img, target=1024):
    w, h = img.size
    scale = target / max(w, h)

    if scale >= 1:
        return img

    new_size = (int(w * scale), int(h * scale))
    return img.resize(new_size, Image.LANCZOS)

def preprocess_image(path):

    img = Image.open(path)
    metadata = img._getexif()
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    img = resize_longest_side(img)
    img = img.convert("RGB")

<<<<<<< HEAD:tools/image_to_text/preprocessing.py
    img.save("tools/image_to_text/preprocessed_image.jpg", quality=95)
    return img, metadata
=======

    img.save((final_path := "app/tools/image_to_text/preprocessed_image.jpg"), quality=95)
    return final_path, img
>>>>>>> origin/main:app/tools/image_to_text/preprocessing.py

if __name__ == "__main__":
    print(preprocess_image("./tools/image_to_text/testing.jpeg"))