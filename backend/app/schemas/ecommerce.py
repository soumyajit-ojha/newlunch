from pydantic import BaseModel
from typing import List, Optional
from app.schemas.product import ProductResponse


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    quantity: int
    product_name_snapshot: str
    price_at_addition: float
    # Optionally include full product details if it still exists
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    total_amount: float
    items: List[CartItemResponse]

    class Config:
        from_attributes = True


class WishlistResponse(BaseModel):
    id: int
    product_id: int
    product: ProductResponse

    class Config:
        from_attributes = True
