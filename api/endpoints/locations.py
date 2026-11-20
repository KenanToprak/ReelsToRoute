import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from core.limiter import limiter
from crud import location as crud_location
from models.user import User
from schemas.location import LocationResponse

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_IMAGE_BYTES = 5 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 64 * 1024


def _detect_image_mime_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


class ReelsInput(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)

    @field_validator("description")
    @classmethod
    def validate_non_whitespace(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Description must not be empty or whitespace only.")
        return stripped


@router.post("/analyze", response_model=LocationResponse)
@limiter.limit("5/minute")
def analyze_reels_and_save(
    request: Request,
    reels_input: ReelsInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sends the Reels description to the AI, finds the location,
    and automatically adds it to a route if it's close to a past location.
    """
    try:
        return crud_location.analyze_and_save_location(
            db=db,
            user_id=current_user.id,
            description=reels_input.description,
        )
    except ValueError as exc:
        logger.warning("AI location analysis failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Yapay Zeka servisi şu an kullanılamıyor, lütfen tekrar deneyin.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error during location save: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An internal database error occurred.",
        ) from exc


@router.post("/analyze-image", response_model=LocationResponse)
@limiter.limit("5/minute")
async def analyze_image_and_save(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a screenshot of a Reel. The Vision AI will identify the location
    and automatically group it into a nearby route.
    """
    chunks: list[bytes] = []
    total_bytes = 0

    while True:
        chunk = await file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 5MB.",
            )
        chunks.append(chunk)

    image_bytes = b"".join(chunks)
    detected_mime = _detect_image_mime_type(image_bytes)
    if detected_mime is None:
        raise HTTPException(
            status_code=400,
            detail="Only valid JPEG or PNG images are allowed.",
        )

    try:
        return await run_in_threadpool(
            crud_location.analyze_and_save_image_location,
            db=db,
            user_id=current_user.id,
            image_bytes=image_bytes,
            mime_type=detected_mime,
        )
    except ValueError as exc:
        logger.warning("AI image analysis failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Yapay Zeka servisi şu an kullanılamıyor, lütfen tekrar deneyin.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error during image location save: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An internal database error occurred.",
        ) from exc


@router.get("/my-locations", response_model=List[LocationResponse])
def get_my_locations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get standalone locations saved by the user.
    """
    return crud_location.get_user_locations(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
