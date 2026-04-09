import os

from fastapi import APIRouter, Request

from ..config import settings
from ..services.model_manager import ModelManager
from ..utils.gpu_utils import get_vram_info, get_device


router = APIRouter(prefix="/api")


def _is_model_cached(model_id: str) -> bool:
    """Check if a model's files exist in the local cache."""
    try:
        cache_path = os.path.join(settings.MODELS_CACHE_DIR, "models--" + model_id.replace("/", "--"))
        return os.path.isdir(cache_path)
    except Exception:
        return False


def _get_current_model_id(request: Request) -> str | None:
    try:
        return request.app.state.model_manager.current_model_id
    except Exception:
        return None


@router.get("/models")
def list_models(request: Request):
    models = ModelManager.get_available_models()
    current_model = _get_current_model_id(request)

    for model in models:
        model["is_loaded"] = model["id"] == current_model
        model["is_cached"] = _is_model_cached(model["id"])

    return models


@router.get("/gpu-status")
def gpu_status(request: Request):
    return {
        "device": get_device(),
        "vram": get_vram_info(),
        "current_model": _get_current_model_id(request),
    }
