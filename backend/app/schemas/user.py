from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from app.models.user import UserRole, AddressType


# from_attributes: Allows Pydantic to read SQLAlchemy models
# User-Auth Schemas
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
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# --- Address Schemas ---
class AddressBase(BaseModel):
    full_name: str
    phone_number: str
    pincode: str
    locality: str
    address_line: str
    city: str
    state: str
    landmark: Optional[str] = None
    alternate_phone: Optional[str] = None
    address_type: AddressType = AddressType.HOME


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: int

    class Config:
        from_attributes = True


# --- Profile Schemas ---
class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    # Note: Profile picture is handled via File Upload, not JSON


# class ProfileResponse(BaseModel):
#     gender: Optional[str]
#     profile_picture: Optional[str]

#     class Config:
#         from_attributes = True


class ProfileResponse(UserBase):
    id: int
    gender: Optional[str] = None
    profile_picture: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def model_validate(cls, obj):
        # This helper maps the nested profile data to the flat schema
        if hasattr(obj, "profile") and obj.profile:
            setattr(obj, 'gender', obj.profile.gender)
            setattr(obj, 'profile_picture', obj.profile.profile_picture)
        return obj

    class Config:
        from_attributes = True
