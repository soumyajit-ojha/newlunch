import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class UserRole(enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"


class User(BaseModel):
    __tablename__ = "users"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.BUYER)
    is_active = Column(Boolean, default=True)

    # Relationship to products (one user can have many products)
    products = relationship("Product", back_populates="seller")
    carts = relationship("Cart", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user")
    profile = relationship("Profile", back_populates="user", uselist=False)  # One-to-one relationship
    addresses = relationship("Address", back_populates="user")  # One-to-many relationship


class AddressType(enum.Enum):
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class Profile(BaseModel):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    gender = Column(String(20), nullable=True)
    profile_picture = Column(String(500), nullable=True)  # S3 URL

    user = relationship("User", back_populates="profile")


class Address(BaseModel):
    __tablename__ = "addresses"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    pincode = Column(String(10), nullable=False)
    locality = Column(String(200), nullable=False)
    address_line = Column(String(500), nullable=False)  # House No, Building, Street
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    landmark = Column(String(200), nullable=True)
    alternate_phone = Column(String(20), nullable=True)
    address_type = Column(Enum(AddressType), default=AddressType.HOME)

    user = relationship("User", back_populates="addresses")
