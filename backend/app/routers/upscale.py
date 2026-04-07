import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.image import GeneratedImage
from ..services.upscaler import Upscaler

router = APIRouter(prefix="/api")

upscaler = Upscaler()


@router.post("/upscale/{image_id}")
def upscale_image(
    image_id: int,
    scale: int = Query(2, ge=2, le=4),
    db: Session = Depends(get_db),
):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = os.path.join(settings.OUTPUTS_DIR, image.file_path)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    result = upscaler.upscale(image_path, scale=scale)

    upscaled_record = GeneratedImage(
        prompt=f"[Upscaled {scale}x] {image.prompt}",
        negative_prompt=image.negative_prompt,
        model_id=image.model_id,
        seed=image.seed,
        steps=image.steps,
        cfg_scale=image.cfg_scale,
        width=result["width"],
        height=result["height"],
        file_path=result["file_path"],
        thumbnail_path=result["thumbnail_path"],
        generation_time=result["upscale_time"],
    )
    db.add(upscaled_record)
    db.commit()
    db.refresh(upscaled_record)

    return {
        "id": upscaled_record.id,
        "prompt": upscaled_record.prompt,
        "negative_prompt": upscaled_record.negative_prompt,
        "model_id": upscaled_record.model_id,
        "seed": upscaled_record.seed,
        "steps": upscaled_record.steps,
        "cfg_scale": upscaled_record.cfg_scale,
        "width": upscaled_record.width,
        "height": upscaled_record.height,
        "file_path": upscaled_record.file_path,
        "thumbnail_path": upscaled_record.thumbnail_path,
        "generation_time": upscaled_record.generation_time,
        "is_favorite": upscaled_record.is_favorite,
        "created_at": upscaled_record.created_at.isoformat(),
    }
