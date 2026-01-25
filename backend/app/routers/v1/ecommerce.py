from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.ecommerce import CartItem, Cart, CartStatus
from app.repositories.ecommerce_repo import EcommerceRepository
from app.schemas.ecommerce import (
    CartResponse,
    CartItemCreate,
    WishlistResponse,
    CartItemUpdate,
)
from app.utils.log_config import logger
from typing import List

router = APIRouter()

# --- CART ENDPOINTS ---


@router.get("/cart", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    logger.info("Get cart: user_id=%s", current_user.id)
    return EcommerceRepository.get_or_create_active_cart(db, current_user.id)


@router.post("/cart/add", response_model=CartResponse)
def add_to_cart(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        "Add to cart: user_id=%s product_id=%s qty=%s",
        current_user.id,
        item_in.product_id,
        item_in.quantity,
    )
    cart = EcommerceRepository.get_or_create_active_cart(db, current_user.id)
    product = db.query(Product).filter(Product.id == item_in.product_id).first()

    if not product or not product.is_active:
        logger.warning(
            "Product not available for cart: product_id=%s", item_in.product_id
        )
        raise HTTPException(status_code=404, detail="Product not available")

    # Check if item already exists in cart
    cart_item = (
        db.query(CartItem).filter_by(cart_id=cart.id, product_id=product.id).first()
    )

    if cart_item:
        cart_item.quantity += item_in.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=item_in.quantity,
            product_name_snapshot=product.model_name,
            price_at_addition=product.price,
        )
        db.add(cart_item)

    db.commit()
    EcommerceRepository.update_cart_total(db, cart)
    logger.info(
        "Added to cart: user_id=%s product_id=%s", current_user.id, item_in.product_id
    )
    return cart


@router.delete("/cart/item/{item_id}")
def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Remove from cart: user_id=%s item_id=%s", current_user.id, item_id)
    cart = EcommerceRepository.get_or_create_active_cart(db, current_user.id)
    item = db.query(CartItem).filter_by(id=item_id, cart_id=cart.id).first()

    if not item:
        logger.warning(
            "Cart item not found: item_id=%s user_id=%s", item_id, current_user.id
        )
        raise HTTPException(status_code=404, detail="Item not found in cart")

    db.delete(item)
    db.commit()
    EcommerceRepository.update_cart_total(db, cart)
    logger.info("Removed from cart: item_id=%s", item_id)
    return {"detail": "Item removed"}


# --- WISHLIST ENDPOINTS ---


@router.post("/wishlist/toggle/{product_id}")
def toggle_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        "Wishlist toggle: user_id=%s product_id=%s", current_user.id, product_id
    )
    added = EcommerceRepository.toggle_wishlist(db, current_user.id, product_id)
    logger.info(
        "Wishlist updated: user_id=%s product_id=%s is_wishlisted=%s",
        current_user.id,
        product_id,
        added,
    )
    return {"is_wishlisted": added, "message": "Wishlist updated"}


@router.get("/wishlist", response_model=List[WishlistResponse])
def get_wishlist(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.models.ecommerce import Wishlist

    logger.info("Get wishlist: user_id=%s", current_user.id)
    items = db.query(Wishlist).filter_by(user_id=current_user.id).all()
    logger.info("Wishlist: %d items for user_id=%s", len(items), current_user.id)
    return items


@router.put("/cart/item/{item_id}", response_model=CartResponse)
def update_cart_item_quantity(
    item_id: int,
    item_update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1. Fetch item and ensure it belongs to the current user's active cart
    item = (
        db.query(CartItem)
        .join(Cart)
        .filter(
            CartItem.id == item_id,
            Cart.user_id == current_user.id,
            Cart.status == CartStatus.CURRENT,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    # 2. Re-verify Stock at DB level (Security check)
    if item.product.stock < item_update.quantity:
        raise HTTPException(
            status_code=400, detail="Requested quantity exceeds available stock"
        )

    # 3. Update quantity
    item.quantity = item_update.quantity
    db.commit()

    # 4. Recalculate Cart Total
    cart = item.cart
    cart.total_amount = sum(i.price_at_addition * i.quantity for i in cart.items)
    db.commit()
    db.refresh(cart)

    return cart
