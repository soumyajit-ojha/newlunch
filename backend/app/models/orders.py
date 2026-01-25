import enum
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class PaymentAttemptStatus(enum.Enum):
    INITIATED = "initiated"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class OrderStatus(enum.Enum):
    INITIATED = "initiated"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Order(BaseModel):
    __tablename__ = "orders"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    address_id = Column(
        Integer, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True
    )
    total_amount = Column(Float, nullable=False)
    order_status = Column(Enum(OrderStatus), default=OrderStatus.INITIATED)
    payment_status = Column(
        Enum(PaymentAttemptStatus), default=PaymentAttemptStatus.INITIATED
    )

    order_items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payment_attempts = relationship("PaymentAttempt", back_populates="order")


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity = Column(Integer, default=1)
    product_name_snapshot = Column(String(200), nullable=False)
    price_per_unit = Column(Float, nullable=False)

    order = relationship("Order", back_populates="order_items")


class PaymentAttempt(BaseModel):
    __tablename__ = "payment_attempts"

    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )

    # Unique strings for S2S
    external_order_id = Column(String(100), unique=True, index=True)
    external_customer_id = Column(String(100))
    idempotency_key = Column(String(100), unique=True)

    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(Enum(PaymentAttemptStatus), default=PaymentAttemptStatus.INITIATED)

    # Store the full response from the S2S app for debugging
    gateway_response = Column(JSON, nullable=True)

    order = relationship("Order", back_populates="payment_attempts")
