from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from api.deps import get_current_user
from crud import location as crud_location
from schemas.location import RouteResponse
from models.user import User

router = APIRouter()

@router.get("/my-routes", response_model=List[RouteResponse])
def get_my_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all automatically generated travel routes (trips) for the user.
    Includes the locations grouped within each route.
    """
    return crud_location.get_user_routes(db=db, user_id=current_user.id)
