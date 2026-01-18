from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.ecommerce import CartItem
from app.repositories.ecommerce_repo import EcommerceRepository
from app.schemas.ecommerce import CartResponse, CartItemCreate, WishlistResponse
from typing import List

router = APIRouter()

# --- CART ENDPOINTS ---


@router.get("/cart", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return EcommerceRepository.get_or_create_active_cart(db, current_user.id)


@router.post("/cart/add", response_model=CartResponse)
def add_to_cart(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = EcommerceRepository.get_or_create_active_cart(db, current_user.id)
    product = db.query(Product).filter(Product.id == item_in.product_id).first()

    if not product or not product.is_active:
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
    return cart


@router.delete("/cart/item/{item_id}")
def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = EcommerceRepository.get_or_create_active_cart(db, current_user.id)
    item = db.query(CartItem).filter_by(id=item_id, cart_id=cart.id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    db.delete(item)
    db.commit()
    EcommerceRepository.update_cart_total(db, cart)
    return {"detail": "Item removed"}


# --- WISHLIST ENDPOINTS ---


@router.post("/wishlist/toggle/{product_id}")
def toggle_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    added = EcommerceRepository.toggle_wishlist(db, current_user.id, product_id)
    return {"is_wishlisted": added, "message": "Wishlist updated"}


@router.get("/wishlist", response_model=List[WishlistResponse])
def get_wishlist(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.models.ecommerce import Wishlist

    return db.query(Wishlist).filter_by(user_id=current_user.id).all()
