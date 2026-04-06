import random

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.image import GeneratedImage
from .websocket import manager

router = APIRouter(prefix="/api")


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    model_id: str = settings.DEFAULT_MODEL
    seed: int = -1
    steps: int = 30
    cfg_scale: float = 7.5
    width: int = 512
    height: int = 512


def _broadcast_progress(step: int, total_steps: int):
    manager.broadcast_sync({"step": step, "total_steps": total_steps})


@router.post("/generate")
def generate_image(req: GenerateRequest, request: Request, db: Session = Depends(get_db)):
    generator = request.app.state.generator

    seed = req.seed if req.seed != -1 else random.randint(0, 2**32 - 1)
    width = min(req.width, settings.MAX_IMAGE_SIZE)
    height = min(req.height, settings.MAX_IMAGE_SIZE)

    result = generator.generate(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        model_id=req.model_id,
        seed=seed,
        steps=req.steps,
        cfg_scale=req.cfg_scale,
        width=width,
        height=height,
        progress_callback=_broadcast_progress,
    )

    image_record = GeneratedImage(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt or None,
        model_id=req.model_id,
        seed=result["seed"],
        steps=req.steps,
        cfg_scale=req.cfg_scale,
        width=width,
        height=height,
        file_path=result["file_path"],
        thumbnail_path=result["thumbnail_path"],
        generation_time=result["generation_time"],
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    return {
        "id": image_record.id,
        "prompt": image_record.prompt,
        "negative_prompt": image_record.negative_prompt,
        "model_id": image_record.model_id,
        "seed": image_record.seed,
        "steps": image_record.steps,
        "cfg_scale": image_record.cfg_scale,
        "width": image_record.width,
        "height": image_record.height,
        "file_path": image_record.file_path,
        "thumbnail_path": image_record.thumbnail_path,
        "generation_time": image_record.generation_time,
        "is_favorite": image_record.is_favorite,
        "created_at": image_record.created_at.isoformat(),
    }
