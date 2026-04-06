import threading

import torch
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline

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
            return cls._instance

    def load_model(self, model_id: str):
        if self.current_model_id == model_id and self.pipeline is not None:
            return

        self.unload_model()

        if "xl" in model_id.lower():
            pipe_cls = StableDiffusionXLPipeline
        else:
            pipe_cls = StableDiffusionPipeline

        self.pipeline = pipe_cls.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            cache_dir=settings.MODELS_CACHE_DIR,
        )

        device = get_device()
        self.pipeline = self.pipeline.to(device)
        self.pipeline.enable_attention_slicing()
        self.current_model_id = model_id

    def unload_model(self):
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self.current_model_id = None
            clear_vram()

    def get_pipeline(self):
        if self.pipeline is None:
            raise RuntimeError("No model is currently loaded. Call load_model() first.")
        return self.pipeline

    @staticmethod
    def get_available_models() -> list[dict]:
        return [
            {
                "id": "stabilityai/stable-diffusion-2-1",
                "name": "Stable Diffusion 2.1",
                "type": "sd",
                "vram": "4 GB",
                "description": "Good quality, fast generation",
            },
            {
                "id": "stabilityai/stable-diffusion-xl-base-1.0",
                "name": "Stable Diffusion XL",
                "type": "sdxl",
                "vram": "7 GB",
                "description": "High quality, detailed images",
            },
        ]
