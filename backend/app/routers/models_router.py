from fastapi import APIRouter, Request

from ..utils.gpu_utils import get_vram_info, get_device

router = APIRouter(prefix="/api")


@router.get("/models")
def list_models(request: Request):
    model_manager = request.app.state.model_manager
    models = model_manager.get_available_models()
    current_model = model_manager.current_model_id

    for model in models:
        model["is_loaded"] = model["id"] == current_model

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
