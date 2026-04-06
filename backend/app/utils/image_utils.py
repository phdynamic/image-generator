import os
import uuid

from PIL import Image


def save_image(image: Image.Image, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath, "PNG")
    return filename


def create_thumbnail(image_path: str, thumbnail_dir: str, size: int = 256) -> str:
    os.makedirs(thumbnail_dir, exist_ok=True)
    image = Image.open(image_path)
    image.thumbnail((size, size))
    filename = f"thumb_{os.path.basename(image_path)}"
    filepath = os.path.join(thumbnail_dir, filename)
    image.save(filepath, "PNG")
    return filename
