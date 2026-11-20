from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from crud import location as crud_location
from models.user import User
from schemas.location import RouteResponse

router = APIRouter()


@router.get("/my-routes", response_model=List[RouteResponse])
def get_my_routes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get automatically generated travel routes (trips) for the user.
    Includes the locations grouped within each route.
    """
    return crud_location.get_user_routes(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
