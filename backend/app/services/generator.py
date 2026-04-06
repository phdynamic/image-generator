import os
import time
from typing import Callable

from huggingface_hub import InferenceClient

from ..config import settings
from ..utils.image_utils import save_image, create_thumbnail
from .model_manager import ModelManager


class ImageGenerator:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.client = None

    def _get_client(self) -> InferenceClient:
        if self.client is None:
            if not settings.HF_TOKEN:
                raise RuntimeError(
                    "HF_TOKEN is not set. Add your HuggingFace token to backend/.env file."
                )
            self.client = InferenceClient(api_key=settings.HF_TOKEN)
        return self.client

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_id: str = settings.DEFAULT_MODEL,
        seed: int = -1,
        steps: int = 30,
        cfg_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        progress_callback: Callable | None = None,
    ) -> dict:
        client = self._get_client()

        if progress_callback:
            progress_callback(1, 3)

        start_time = time.time()

        image = client.text_to_image(
            prompt=prompt,
            model=model_id,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=cfg_scale,
            negative_prompt=negative_prompt if negative_prompt else None,
        )

        if progress_callback:
            progress_callback(2, 3)

        generation_time = time.time() - start_time

        filename = save_image(image, settings.OUTPUTS_DIR)
        image_path = os.path.join(settings.OUTPUTS_DIR, filename)
        thumbnail_filename = create_thumbnail(
            image_path, settings.THUMBNAILS_DIR, settings.THUMBNAIL_SIZE
        )

        if progress_callback:
            progress_callback(3, 3)

        return {
            "file_path": filename,
            "thumbnail_path": thumbnail_filename,
            "seed": seed,
            "generation_time": round(generation_time, 2),
        }
