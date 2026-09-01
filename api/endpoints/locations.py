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

@router.get("/my-locations", response_model=List[LocationResponse])
def get_my_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all standalone locations saved by the user.
    """
    return crud_location.get_user_locations(db=db, user_id=current_user.id)
