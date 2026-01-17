from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    role: UserRole = UserRole.BUYER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True  # Allows Pydantic to read SQLAlchemy models


class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
