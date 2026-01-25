from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.stripe_service import StripeService
from app.services.order_service import OrderService
import logging

logger = logging.getLogger("sellphone.webhooks")
router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    payload = await request.body()

    # 1. Verify the event
    event = StripeService.verify_webhook(payload, stripe_signature)
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Handle Payment Success
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")

        if order_id:
            # ATOMIC UPDATE: Confirm Order & Deduct Stock
            processed = OrderService.finalize_payment_success(db, int(order_id))
            if processed:
                logger.info(f"✅ Order {order_id} successfully confirmed via Webhook")
            else:
                logger.warning(
                    f"⚠️ Webhook received for order {order_id} but it was already processed."
                )

    # 3. Handle Payment Failure
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")
        if order_id:
            OrderService.handle_payment_failure(db, int(order_id))
            logger.error(f"❌ Payment failed for Order {order_id}")

    return {"status": "success"}
