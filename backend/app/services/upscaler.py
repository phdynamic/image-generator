import os
import time

from PIL import Image

from ..config import settings
from ..utils.image_utils import save_image, create_thumbnail


class Upscaler:
    def upscale(self, image_path: str, scale: int = 2) -> dict:
        """Upscale an image using Lanczos resampling.

        Uses high-quality Pillow resampling. Real-ESRGAN can be added later
        for AI-powered upscaling when the dependency is available.
        """
        start_time = time.time()

        image = Image.open(image_path)
        new_width = image.width * scale
        new_height = image.height * scale
        upscaled = image.resize((new_width, new_height), Image.LANCZOS)

        filename = save_image(upscaled, settings.OUTPUTS_DIR)
        output_path = os.path.join(settings.OUTPUTS_DIR, filename)
        thumbnail_filename = create_thumbnail(
            output_path, settings.THUMBNAILS_DIR, settings.THUMBNAIL_SIZE
        )

        upscale_time = time.time() - start_time

        return {
            "file_path": filename,
            "thumbnail_path": thumbnail_filename,
            "width": new_width,
            "height": new_height,
            "upscale_time": round(upscale_time, 2),
        }
