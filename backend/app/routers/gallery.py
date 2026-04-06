import os
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..config import settings
from ..database import get_db
from ..models.image import GeneratedImage

router = APIRouter(prefix="/api")


@router.get("/images")
def list_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(GeneratedImage)

    if search:
        query = query.filter(GeneratedImage.prompt.ilike(f"%{search}%"))

    if favorites_only:
        query = query.filter(GeneratedImage.is_favorite == True)

    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 1

    images = (
        query.order_by(desc(GeneratedImage.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "images": [_serialize_image(img) for img in images],
        "total": total,
        "page": page,
        "pages": pages,
    }


@router.get("/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return _serialize_image(image)


@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = os.path.join(settings.OUTPUTS_DIR, image.file_path)
    if os.path.exists(image_path):
        os.remove(image_path)

    if image.thumbnail_path:
        thumb_path = os.path.join(settings.THUMBNAILS_DIR, image.thumbnail_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    db.delete(image)
    db.commit()
    return {"detail": "Image deleted"}


@router.post("/images/{image_id}/favorite")
def toggle_favorite(image_id: int, db: Session = Depends(get_db)):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.is_favorite = not image.is_favorite
    db.commit()
    db.refresh(image)
    return _serialize_image(image)


def _serialize_image(image: GeneratedImage) -> dict:
    return {
        "id": image.id,
        "prompt": image.prompt,
        "negative_prompt": image.negative_prompt,
        "model_id": image.model_id,
        "seed": image.seed,
        "steps": image.steps,
        "cfg_scale": image.cfg_scale,
        "width": image.width,
        "height": image.height,
        "file_path": image.file_path,
        "thumbnail_path": image.thumbnail_path,
        "generation_time": image.generation_time,
        "is_favorite": image.is_favorite,
        "created_at": image.created_at.isoformat(),
    }
