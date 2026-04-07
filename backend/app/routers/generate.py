import random

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from PIL import Image
import io

from ..config import settings
from ..database import get_db
from ..models.image import GeneratedImage
from .websocket import manager

router = APIRouter(prefix="/api")


def _broadcast_progress(step: int, total_steps: int):
    manager.broadcast_sync({"step": step, "total_steps": total_steps})


@router.post("/generate")
def generate_image(
    request: Request,
    db: Session = Depends(get_db),
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    model_id: str = Form(settings.DEFAULT_MODEL),
    seed: int = Form(-1),
    steps: int = Form(30),
    cfg_scale: float = Form(7.5),
    width: int = Form(512),
    height: int = Form(512),
    strength: float = Form(0.75),
    input_image: UploadFile | None = File(None),
):
    generator = request.app.state.generator

    actual_seed = seed if seed != -1 else random.randint(0, 2**32 - 1)
    actual_width = min(width, settings.MAX_IMAGE_SIZE)
    actual_height = min(height, settings.MAX_IMAGE_SIZE)

    # Load input image if provided
    pil_image = None
    if input_image is not None and input_image.size > 0:
        image_data = input_image.file.read()
        pil_image = Image.open(io.BytesIO(image_data))

    result = generator.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        model_id=model_id,
        seed=actual_seed,
        steps=steps,
        cfg_scale=cfg_scale,
        width=actual_width,
        height=actual_height,
        input_image=pil_image,
        strength=strength,
        progress_callback=_broadcast_progress,
    )

    image_record = GeneratedImage(
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        model_id=model_id,
        seed=result["seed"],
        steps=steps,
        cfg_scale=cfg_scale,
        width=actual_width,
        height=actual_height,
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
