from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    source_image_url: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: int
    user_id: int
    route_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteBase(BaseModel):
    name: str
    estimated_days: int = Field(default=1, ge=1)


class RouteCreate(RouteBase):
    pass


class RouteResponse(RouteBase):
    id: int
    user_id: int
    created_at: datetime
    locations: List[LocationResponse] = []

    model_config = ConfigDict(from_attributes=True)
