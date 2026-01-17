import enum
from sqlalchemy import Column, String, Enum, Boolean
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
