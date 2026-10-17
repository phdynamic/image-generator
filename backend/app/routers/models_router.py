from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..services import model_cache
from ..services.downloads import DownloadBusy, download_manager
from ..services.hf_auth import gated_message, hf_token_available
from ..services.model_manager import ModelManager
from ..services.model_registry import get_spec, gpu_problem
from ..utils.gpu_utils import get_device, get_gpu_name, get_vram_info


router = APIRouter(prefix="/api")

# Leave some room for the unpacked files and the model's own temp data.
DISK_SPACE_MARGIN = 1.1


class ModelRequest(BaseModel):
    model_id: str


def _get_current_model_id(request: Request) -> str | None:
    try:
        return request.app.state.model_manager.current_model_id
    except Exception:
        return None


def _require_spec(model_id: str):
    spec = get_spec(model_id)
    if spec is None:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_id}")
    return spec


@router.get("/models")
def list_models(request: Request):
    models = ModelManager.get_available_models()
    current_model = _get_current_model_id(request)
    token_available = hf_token_available()
    total_vram = (get_vram_info() or {}).get("total")

    for model in models:
        problem = gpu_problem(get_spec(model["id"]), total_vram)
        model["fits_gpu"] = problem is None
        model["gpu_problem"] = problem
        model["needs_token"] = bool(model["gated"]) and not token_available
        model["is_loaded"] = model["id"] == current_model
        model["is_cached"] = model_cache.is_cached(model["id"])
        model["download"] = download_manager.state(model["id"])

    return models


@router.post("/models/download", status_code=202)
def start_download(req: ModelRequest, request: Request):
    spec = _require_spec(req.model_id)

    if model_cache.is_cached(spec.id):
        raise HTTPException(status_code=409, detail=f"{spec.name} is already downloaded.")

    problem = gpu_problem(spec, (get_vram_info() or {}).get("total"))
    if problem:
        raise HTTPException(status_code=400, detail=problem)

    if spec.gated and not hf_token_available():
        raise HTTPException(status_code=400, detail=gated_message(spec.id, token_set=False))

    if spec.download_gb:
        needed = spec.download_gb * model_cache.GIB
        already = model_cache.cache_size(spec.id)
        if model_cache.free_disk_bytes() < (needed - already) * DISK_SPACE_MARGIN:
            raise HTTPException(
                status_code=507,
                detail=f"Not enough disk space for {spec.name} (needs about {spec.download_gb:g} GB).",
            )

    download_manager.clear(spec.id)  # forget an earlier failure
    model_manager = request.app.state.model_manager
    try:
        download_manager.start(spec, model_manager.download_model)
    except DownloadBusy as busy:
        other = get_spec(busy.active_model_id)
        raise HTTPException(
            status_code=409,
            detail=f"Another download is in progress ({other.name if other else busy.active_model_id}).",
        )
    return {"status": "downloading"}


@router.post("/models/delete")
def delete_model(req: ModelRequest, request: Request):
    spec = _require_spec(req.model_id)

    if download_manager.active() == spec.id:
        raise HTTPException(status_code=409, detail="That model is still downloading.")

    generator = request.app.state.generator
    # Don't pull files out from under an image that's being generated.
    if not generator.lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="An image is being generated. Try again in a moment.")
    try:
        manager = request.app.state.model_manager
        if manager.current_model_id == spec.id:
            manager.unload_model()
        model_cache.delete(spec.id)
    finally:
        generator.lock.release()
    return {"deleted": spec.id}


@router.get("/gpu-status")
def gpu_status(request: Request):
    return {
        "device": get_device(),
        "name": get_gpu_name(),
        "vram": get_vram_info(),
        "current_model": _get_current_model_id(request),
    }
