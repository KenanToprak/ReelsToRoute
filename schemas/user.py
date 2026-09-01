from pydantic import BaseModel, EmailStr
from typing import Optional

# Shared properties (for both reading and writing)
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Properties to receive when creating a new user
class UserCreate(UserBase):
    password: str

# Properties to return to the client (password excluded!)
class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
