import os

from fastapi import APIRouter, Request

from ..config import settings
from ..utils.gpu_utils import get_vram_info, get_device


router = APIRouter(prefix="/api")


def _is_model_cached(model_id: str) -> bool:
    """Check if a model's files exist in the local cache."""
    cache_path = os.path.join(settings.MODELS_CACHE_DIR, "models--" + model_id.replace("/", "--"))
    return os.path.isdir(cache_path)


@router.get("/models")
def list_models(request: Request):
    model_manager = request.app.state.model_manager
    models = model_manager.get_available_models()
    current_model = model_manager.current_model_id

    for model in models:
        model["is_loaded"] = model["id"] == current_model
        model["is_cached"] = _is_model_cached(model["id"])

    return models


@router.get("/gpu-status")
def gpu_status(request: Request):
    model_manager = request.app.state.model_manager
    vram = get_vram_info()
    return {
        "device": get_device(),
        "vram": vram,
        "current_model": model_manager.current_model_id,
    }
