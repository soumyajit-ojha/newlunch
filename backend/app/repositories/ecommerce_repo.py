from sqlalchemy.orm import Session
from app.models.ecommerce import Cart, CartItem, CartStatus, Wishlist
from app.models.product import Product
from app.utils.log_config import logger


class EcommerceRepository:
    @staticmethod
    def get_or_create_active_cart(db: Session, user_id: int) -> Cart:
        cart = (
            db.query(Cart)
            .filter(Cart.user_id == user_id, Cart.status == CartStatus.CURRENT)
            .first()
        )

        if not cart:
            cart = Cart(user_id=user_id, status=CartStatus.CURRENT)
            db.add(cart)
            db.commit()
            db.refresh(cart)
            logger.info("EcommerceRepository: created new cart for user_id=%s cart_id=%s", user_id, cart.id)
        return cart

    @staticmethod
    def update_cart_total(db: Session, cart: Cart):
        total = sum(item.price_at_addition * item.quantity for item in cart.items)
        cart.total_amount = total
        db.commit()

    @staticmethod
    def toggle_wishlist(db: Session, user_id: int, product_id: int):
        existing = (
            db.query(Wishlist).filter_by(user_id=user_id, product_id=product_id).first()
        )
        if existing:
            db.delete(existing)
            db.commit()
            return False  # Removed

        new_item = Wishlist(user_id=user_id, product_id=product_id)
        db.add(new_item)
        db.commit()
        return True  # Added
