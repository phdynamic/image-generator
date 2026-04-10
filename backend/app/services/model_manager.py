import threading

import torch
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionImg2ImgPipeline,
    StableDiffusionXLImg2ImgPipeline,
)

from ..config import settings
from ..utils.gpu_utils import get_device, clear_vram


class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.current_model_id = None
                cls._instance.pipeline = None
                cls._instance.img2img_pipeline = None
                cls._instance._load_lock = threading.Lock()
            return cls._instance

    def load_model(self, model_id: str):
        with self._load_lock:
            if self.current_model_id == model_id and self.pipeline is not None:
                return

            self.unload_model()

            is_xl = "xl" in model_id.lower() or "ssd" in model_id.lower()
            pipe_cls = StableDiffusionXLPipeline if is_xl else StableDiffusionPipeline
            img2img_cls = StableDiffusionXLImg2ImgPipeline if is_xl else StableDiffusionImg2ImgPipeline

            # Disable safety checker: not needed for personal use and it
            # requires reading diffusers .py source files at runtime, which
            # fails inside a PyInstaller frozen bundle.
            kwargs = {
                "torch_dtype": torch.float16,
                "cache_dir": settings.MODELS_CACHE_DIR,
            }
            if not is_xl:
                kwargs["safety_checker"] = None
                kwargs["requires_safety_checker"] = False

            self.pipeline = pipe_cls.from_pretrained(model_id, **kwargs)

            device = get_device()
            self.pipeline = self.pipeline.to(device)
            self.pipeline.enable_attention_slicing()

            # Create img2img pipeline sharing the same model components
            self.img2img_pipeline = img2img_cls(**self.pipeline.components)

            self.current_model_id = model_id

    def unload_model(self):
        if self.pipeline is not None:
            del self.pipeline
            del self.img2img_pipeline
            self.pipeline = None
            self.img2img_pipeline = None
            self.current_model_id = None
            clear_vram()

    def get_pipeline(self):
        if self.pipeline is None:
            raise RuntimeError("No model is currently loaded. Call load_model() first.")
        return self.pipeline

    def get_img2img_pipeline(self):
        if self.img2img_pipeline is None:
            raise RuntimeError("No model is currently loaded. Call load_model() first.")
        return self.img2img_pipeline

    @staticmethod
    def get_available_models() -> list[dict]:
        return [
            {
                "id": "Lykon/dreamshaper-8",
                "name": "DreamShaper 8",
                "type": "sd",
                "vram": "4 GB",
                "description": "Excellent quality, versatile style, great for illustrations",
            },
            {
                "id": "segmind/SSD-1B",
                "name": "Segmind SSD-1B (SDXL Distilled)",
                "type": "sdxl",
                "vram": "5 GB",
                "description": "Fast SDXL quality at lower VRAM, great detail",
            },
            {
                "id": "stabilityai/sdxl-turbo",
                "name": "SDXL Turbo",
                "type": "sdxl",
                "vram": "6 GB",
                "description": "Near-instant generation (1-4 steps), good quality",
            },
        ]
