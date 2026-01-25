from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any
from app.models.orders import OrderStatus, PaymentAttemptStatus


# --- Shared Schemas ---


class OrderItemBase(BaseModel):
    product_id: Optional[int]
    quantity: int = Field(..., gt=0)  # Must be greater than 0
    product_name_snapshot: str
    price_per_unit: float

    class Config:
        from_attributes = True


# --- Request Schemas (Input) ---


class CheckoutRequest(BaseModel):
    """
    Input for the /checkout endpoint.
    User selects an address and specific items from their cart.
    """

    address_id: int
    cart_item_ids: List[int] = Field(..., min_items=1)


class OrderCreate(BaseModel):
    """Internal use for creating an order record"""

    address_id: int
    user_id: int
    total_amount: float


class PaymentWebhookPayload(BaseModel):
    """
    Schema for the S2S Callback.
    The Payment App sends this to our /webhook/payment endpoint.
    """

    external_order_id: str
    status: str  # 'success' or 'failed'
    # Optional: include raw metadata if needed
    metadata: Optional[dict] = None


# --- Response Schemas (Output) ---


class OrderItemResponse(OrderItemBase):
    id: int


class PaymentAttemptResponse(BaseModel):
    """
    Used for auditing. Usually shown in Admin panels or
    detailed order history.
    """

    external_order_id: str
    idempotency_key: str
    amount: float
    currency: str
    status: PaymentAttemptStatus
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """
    The main Order view for the Buyer (Orders Page).
    """

    id: int
    address_id: Optional[int]
    total_amount: float
    order_status: OrderStatus
    payment_status: PaymentAttemptStatus
    created_at: datetime
    updated_at: Optional[datetime]

    # Nested Items
    order_items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    """
    The response sent back to React immediately after clicking "Place Order".
    Contains the order metadata and the data required to trigger Stripe.
    """

    order: OrderResponse
    # This is the JSON response from your S2S Payment Gateway App
    payment_intent_data: Optional[Any]
