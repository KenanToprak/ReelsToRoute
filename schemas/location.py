from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    source_image_url: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    user_id: int
    route_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RouteBase(BaseModel):
    name: str
    estimated_days: int = 1

class RouteCreate(RouteBase):
    pass

class RouteResponse(RouteBase):
    id: int
    user_id: int
    created_at: datetime
    locations: List[LocationResponse] = []

    class Config:
        from_attributes = True
