from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Shared properties (for both reading and writing)
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


# Properties to receive when creating a new user
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_byte_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


# Properties to return to the client (password excluded!)
class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
