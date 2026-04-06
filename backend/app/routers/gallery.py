import os
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

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
    sort_by: str = "newest",
    model_filter: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(GeneratedImage)

    if search:
        query = query.filter(GeneratedImage.prompt.ilike(f"%{search}%"))

    if favorites_only:
        query = query.filter(GeneratedImage.is_favorite == True)

    if model_filter:
        query = query.filter(GeneratedImage.model_id == model_filter)

    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 1

    if sort_by == "oldest":
        query = query.order_by(asc(GeneratedImage.created_at))
    elif sort_by == "model":
        query = query.order_by(asc(GeneratedImage.model_id), desc(GeneratedImage.created_at))
    else:
        query = query.order_by(desc(GeneratedImage.created_at))

    images = query.offset((page - 1) * per_page).limit(per_page).all()

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

    _remove_image_files(image)
    db.delete(image)
    db.commit()
    return {"detail": "Image deleted"}


class BatchDeleteRequest(BaseModel):
    ids: list[int]


@router.post("/images/batch-delete")
def batch_delete_images(req: BatchDeleteRequest, db: Session = Depends(get_db)):
    images = db.query(GeneratedImage).filter(GeneratedImage.id.in_(req.ids)).all()
    for image in images:
        _remove_image_files(image)
        db.delete(image)
    db.commit()
    return {"detail": f"Deleted {len(images)} images"}


@router.post("/images/{image_id}/favorite")
def toggle_favorite(image_id: int, db: Session = Depends(get_db)):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.is_favorite = not image.is_favorite
    db.commit()
    db.refresh(image)
    return _serialize_image(image)


@router.get("/prompts/history")
def prompt_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return unique recent prompts for the history sidebar."""
    results = (
        db.query(GeneratedImage.prompt)
        .group_by(GeneratedImage.prompt)
        .order_by(desc(GeneratedImage.created_at))
        .limit(limit)
        .all()
    )
    return [r[0] for r in results]


def _remove_image_files(image: GeneratedImage):
    image_path = os.path.join(settings.OUTPUTS_DIR, image.file_path)
    if os.path.exists(image_path):
        os.remove(image_path)
    if image.thumbnail_path:
        thumb_path = os.path.join(settings.THUMBNAILS_DIR, image.thumbnail_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)


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
