from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class BaseModel(Base):
    __abstract__ = True  # Tells SQLAlchemy not to create a table for this
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
