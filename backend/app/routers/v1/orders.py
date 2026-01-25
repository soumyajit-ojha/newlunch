from fastapi import APIRouter, Depends, Body, Header, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.deps import get_current_user
from app.services.order_service import OrderService
from app.schemas.orders import (
    CheckoutRequest,
    OrderResponse,
)  # Schema: {address_id: int, cart_item_ids: list[int]}

router = APIRouter()


@router.post("/checkout")
async def create_order(
    req: CheckoutRequest, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    return await OrderService.initiate_checkout(
        db, user, req.address_id, req.cart_item_ids
    )


@router.post("/webhook/payment")
async def payment_webhook(
    payload: dict = Body(...),
    x_api_key: str = Header(None),  # Security: S2S App should also send its key back
    db: Session = Depends(get_db),
):
    """
    S2S Webhook: Your Payment App calls this.
    Expected Payload: {"external_order_id": "...", "status": "success" | "failed"}
    """
    # Simple Security check
    # if x_api_key != settings.INTERNAL_WEBHOOK_SECRET: raise HTTPException(403)
    if x_api_key != settings.INTERNAL_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized Webhook Source")

    external_order_id = payload.get("external_order_id")
    status = payload.get("status")  # "success"
    processed = OrderService.process_payment_webhook(
        db, external_order_id=external_order_id, success=(status == "success")
    )

    if not processed:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"message": "Order Confirmed and Stock Adjusted"}


@router.get("/my-orders")
def get_my_orders(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.orders import Order

    return (
        db.query(Order)
        .filter_by(user_id=user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_details(
    order_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.models.orders import Order

    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
