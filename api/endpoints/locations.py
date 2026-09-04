from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from api.deps import get_current_user
from crud import location as crud_location
from schemas.location import LocationResponse
from models.user import User

router = APIRouter()

class ReelsInput(BaseModel):
    description: str

@router.post("/analyze", response_model=LocationResponse)
def analyze_reels_and_save(
    reels_input: ReelsInput, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sends the Reels description to the AI, finds the location, 
    and automatically adds it to a route if it's close to a past location.
    """
    return crud_location.analyze_and_save_location(db=db, user_id=current_user.id, description=reels_input.description)

from fastapi import UploadFile, File, HTTPException

@router.post("/analyze-image", response_model=LocationResponse)
async def analyze_image_and_save(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a screenshot of a Reel. The Vision AI will identify the location 
    and automatically group it into a nearby route.
    """
    # 1. Dosya Uzantısı/Tipi Kontrolü (Güvenlik)
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG or PNG images are allowed.")
        
    # 2. Dosya Boyutu Kontrolü (Güvenlik - Max 5MB)
    image_bytes = await file.read()
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")
        
    return crud_location.analyze_and_save_image_location(db=db, user_id=current_user.id, image_bytes=image_bytes)

@router.get("/my-locations", response_model=List[LocationResponse])
def get_my_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all standalone locations saved by the user.
    """
    return crud_location.get_user_locations(db=db, user_id=current_user.id)
