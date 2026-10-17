import io
import random

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from PIL import Image

from ..config import settings
from ..database import SessionLocal
from ..models.image import GeneratedImage
from ..services.jobs import JobError, job_manager
from ..services.model_registry import get_spec
from .websocket import manager

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_QUEUED_JOBS = 20
MIN_SIZE = 256


def _broadcast_progress(step: int, total_steps: int):
    manager.broadcast_sync({"step": step, "total_steps": total_steps})


def _snap_size(value: int) -> int:
    """Clamp to the allowed range and round down to a multiple of 16."""
    value = max(MIN_SIZE, min(value, settings.MAX_IMAGE_SIZE))
    return value - value % 16


def _load_upload(upload: UploadFile) -> Image.Image:
    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large (15 MB max)")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        raise HTTPException(status_code=400, detail="That file isn't a readable image")
    return image


def _serialize(record: GeneratedImage) -> dict:
    return {
        "id": record.id,
        "prompt": record.prompt,
        "negative_prompt": record.negative_prompt,
        "model_id": record.model_id,
        "seed": record.seed,
        "steps": record.steps,
        "cfg_scale": record.cfg_scale,
        "width": record.width,
        "height": record.height,
        "file_path": record.file_path,
        "thumbnail_path": record.thumbnail_path,
        "generation_time": record.generation_time,
        "is_favorite": record.is_favorite,
        "created_at": record.created_at.isoformat(),
    }


def _run_generation(generator, params: dict) -> dict:
    """Runs on the job worker thread: generate, then save the gallery record."""
    try:
        result = generator.generate(progress_callback=_broadcast_progress, **params)
    except RuntimeError as exc:
        # e.g. missing optional packages
        raise JobError(str(exc))
    except Exception as exc:
        if "out of memory" in str(exc).lower():
            raise JobError(
                "The GPU ran out of memory. Try a smaller image size, "
                "close other GPU programs, or pick a lighter model.",
                507,
            )
        raise

    db = SessionLocal()
    try:
        record = GeneratedImage(
            prompt=params["prompt"],
            negative_prompt=params["negative_prompt"] or None,
            model_id=params["model_id"],
            seed=result["seed"],
            steps=result["steps"],
            cfg_scale=result["cfg_scale"],
            width=params["width"],
            height=params["height"],
            file_path=result["file_path"],
            thumbnail_path=result["thumbnail_path"],
            generation_time=result["generation_time"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _serialize(record)
    finally:
        db.close()


@router.post("/generate", status_code=202)
def generate_image(
    request: Request,
    prompt: str = Form(..., max_length=4000),
    negative_prompt: str = Form("", max_length=4000),
    model_id: str = Form(settings.DEFAULT_MODEL),
    seed: int = Form(-1),
    steps: int = Form(30),
    cfg_scale: float = Form(7.5),
    width: int = Form(512),
    height: int = Form(512),
    strength: float = Form(0.75),
    input_image: UploadFile | None = File(None),
):
    """Queues an image for generation. Poll GET /api/jobs/{job_id} for the result."""
    if get_spec(model_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_id}")
    if job_manager.queued_count() >= MAX_QUEUED_JOBS:
        raise HTTPException(status_code=429, detail="Too many images queued. Wait for some to finish.")

    pil_image = None
    if input_image is not None and input_image.size:
        pil_image = _load_upload(input_image)

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "model_id": model_id,
        "seed": seed if seed != -1 else random.randint(0, 2**32 - 1),
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": _snap_size(width),
        "height": _snap_size(height),
        "input_image": pil_image,
        "strength": min(max(strength, 0.05), 1.0),
    }
    generator = request.app.state.generator
    job_id = job_manager.submit(lambda: _run_generation(generator, params))
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = job_manager.snapshot(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found (the server may have restarted)")
    return job
