import gc
import os
import threading
import time
import traceback
from typing import Callable

from PIL import Image

from ..config import settings
from ..utils.image_utils import save_image, create_thumbnail
from ..utils.gpu_utils import clear_vram, get_device
from .model_manager import ModelManager
from .model_registry import get_spec


class ImageGenerator:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        # One GPU: generate one image at a time, whoever asks.
        self.lock = threading.Lock()

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
        input_image: Image.Image | None = None,
        strength: float = 0.75,
        progress_callback: Callable | None = None,
    ) -> dict:
        import torch

        spec = get_spec(model_id)
        if spec is None:
            raise ValueError(f"Unknown model: {model_id}")

        steps = max(1, min(steps, spec.max_steps))
        guidance = spec.fixed_cfg if spec.fixed_cfg is not None else cfg_scale

        def step_callback(pipe, step_index, timestep, callback_kwargs):
            if progress_callback:
                progress_callback(step_index + 1, steps)
            return callback_kwargs

        with self.lock:
            self.model_manager.load_model(model_id)
            generator = torch.Generator(device=get_device()).manual_seed(seed)

            call = {
                "prompt": prompt,
                "num_inference_steps": steps,
                "guidance_scale": guidance,
                "generator": generator,
                "callback_on_step_end": step_callback,
            }
            if spec.supports_negative and negative_prompt:
                call["negative_prompt"] = negative_prompt

            start_time = time.time()

            if input_image is not None:
                pipeline = self.model_manager.get_img2img_pipeline()
                call["image"] = input_image.convert("RGB").resize((width, height))
                # Strength must leave at least one denoising step.
                call["strength"] = max(strength, 1.0 / steps + 1e-6)
            else:
                pipeline = self.model_manager.get_pipeline()
                call["width"] = width
                call["height"] = height

            try:
                result = pipeline(**call)
            except BaseException as exc:
                # Give back the memory a failed run was holding so a retry
                # (or another model) starts with all the free VRAM it can get.
                traceback.clear_frames(exc.__traceback__)
                gc.collect()
                clear_vram()
                raise
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
            "steps": steps,
            "cfg_scale": guidance,
            "generation_time": round(generation_time, 2),
        }
