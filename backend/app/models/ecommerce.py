import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CartStatus(enum.Enum):
    CURRENT = "current"  # Active shopping cart
    ORDERED = "ordered"  # Converted to an order
    ABANDONED = "abandoned"


class Cart(BaseModel):
    __tablename__ = "carts"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(Enum(CartStatus), default=CartStatus.CURRENT)
    total_amount = Column(Float, default=0.0)

    user = relationship("User", back_populates="carts")
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(BaseModel):
    __tablename__ = "cart_items"

    cart_id = Column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity = Column(Integer, default=1)

    # SNAPSHOTS: Prevent data loss if product is updated/deleted
    product_name_snapshot = Column(String(200))
    price_at_addition = Column(Float)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class Wishlist(BaseModel):
    __tablename__ = "wishlist"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )

    # Prevent duplicate wishlist entries
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="_user_product_wishlist_uc"),
    )

    user = relationship("User", back_populates="wishlist")
    product = relationship("Product")
