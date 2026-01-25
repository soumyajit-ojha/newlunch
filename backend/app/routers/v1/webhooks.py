import stripe
import logging
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.services.order_service import OrderService

logger = logging.getLogger("sellphone.webhooks")
router = APIRouter()

# Official Stripe Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    The Official Entry Point for Stripe signals.
    """
    payload = await request.body()

    try:
        # 1. Verify that this signal REALLY came from Stripe
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Webhook Signature Verification Failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Extract Data from Event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]  # Stripe object

        # This is the pi_... ID you saw in your logs
        stripe_intent_id = payment_intent["id"]

        logger.info(f"💰 Webhook: Payment received for {stripe_intent_id}")

        # 3. Trigger Fulfillment Logic
        # We use the Stripe ID to find our PaymentAttempt record
        success = OrderService.finalize_payment_success(db, stripe_intent_id)

        if not success:
            logger.error(f"Fulfillment failed for Stripe ID: {stripe_intent_id}")

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        OrderService.handle_payment_failure(db, payment_intent["id"])

    return {"status": "success"}
