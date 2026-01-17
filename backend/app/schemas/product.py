from pydantic import BaseModel
from typing import Optional, List


class ProductBase(BaseModel):
    brand: str
    model_name: str
    price: float
    stock: int = 0
    description: Optional[str] = None
    ram: int
    rom: int
    network_type: str
    processor: str
    battery: int
    screen_size: float


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    image_url: Optional[str]
    is_active: bool
    seller_id: int

    class Config:
        from_attributes = True


class FilterOptionsResponse(BaseModel):
    brands: List[str]
    ram_options: List[int]
    network_types: List[str]
    max_price_limit: float
