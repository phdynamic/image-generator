import threading

from ..config import settings


class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.current_model_id = None
            return cls._instance

    @staticmethod
    def get_available_models() -> list[dict]:
        return [
            {
                "id": "stabilityai/stable-diffusion-3.5-medium",
                "name": "Stable Diffusion 3.5 Medium",
                "type": "cloud",
                "vram": "Cloud",
                "description": "High quality, runs via HuggingFace API",
            },
            {
                "id": "stabilityai/stable-diffusion-xl-base-1.0",
                "name": "Stable Diffusion XL",
                "type": "cloud",
                "vram": "Cloud",
                "description": "Great for detailed images, runs via HuggingFace API",
            },
            {
                "id": "black-forest-labs/FLUX.1-schnell",
                "name": "FLUX.1 Schnell",
                "type": "cloud",
                "vram": "Cloud",
                "description": "Fast, excellent quality, runs via HuggingFace API",
            },
        ]
