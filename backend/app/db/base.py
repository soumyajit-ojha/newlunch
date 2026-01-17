# Import all models here so Alembic can find them
from app.db.session import Base
from app.models.user import User
from app.models.product import Product
from app.models.ecommerce import Cart, CartItem, Wishlist

# Later: from app.models.products import Product
