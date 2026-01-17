from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    # Core Product Info
    brand = Column(String(100), index=True, nullable=False)
    model_name = Column(String(200), index=True, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    description = Column(String(1000))
    image_url = Column(String(500))  # S3 URL

    # Mobile Specific Specs (Filtering)
    ram = Column(Integer)  # GB
    rom = Column(Integer)  # GB
    network_type = Column(String(50))  # 5G, 4G
    processor = Column(String(100))
    battery = Column(Integer)  # mAh
    screen_size = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)

    # Ownership
    seller_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    seller = relationship("User", back_populates="products")
