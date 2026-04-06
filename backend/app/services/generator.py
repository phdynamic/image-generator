import os
import time
from typing import Callable

import torch

from ..config import settings
from ..utils.image_utils import save_image, create_thumbnail
from ..utils.gpu_utils import get_device
from .model_manager import ModelManager


class ImageGenerator:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

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
        self.model_manager.load_model(model_id)
        pipeline = self.model_manager.get_pipeline()

        device = get_device()
        generator = torch.Generator(device=device).manual_seed(seed)

        def step_callback(pipe, step_index, timestep, callback_kwargs):
            if progress_callback:
                progress_callback(step_index + 1, steps)
            return callback_kwargs

        start_time = time.time()

        result = pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            num_inference_steps=steps,
            guidance_scale=cfg_scale,
            width=width,
            height=height,
            generator=generator,
            callback_on_step_end=step_callback,
        )

        generation_time = time.time() - start_time
        image = result.images[0]

        filename = save_image(image, settings.OUTPUTS_DIR)
        image_path = os.path.join(settings.OUTPUTS_DIR, filename)
        thumbnail_filename = create_thumbnail(
            image_path, settings.THUMBNAILS_DIR, settings.THUMBNAIL_SIZE
        )

        return {
            "file_path": filename,
            "thumbnail_path": thumbnail_filename,
            "seed": seed,
            "generation_time": round(generation_time, 2),
        }
