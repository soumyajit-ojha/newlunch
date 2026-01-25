import stripe
import uuid
import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.orders import PaymentAttempt, PaymentAttemptStatus

logger = logging.getLogger("sellphone.payments")

# Use your Stripe Secret Key directly
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    @staticmethod
    async def create_payment_intent(db: Session, order, user):
        """
        DIRECT STRIPE INTEGRATION:
        Creates a PaymentIntent directly on Stripe's servers.
        """
        # 1. Generate local identifiers
        # We still generate an external_order_id for our own internal tracking
        ext_order_id = f"SP-ORD-{order.id}-{uuid.uuid4().hex[:6]}"

        try:
            # 2. Call Stripe API
            # Stripe amount is in cents (integer)
            amount_in_cents = int(order.total_amount * 100)

            logger.info(f"Initiating direct Stripe PaymentIntent for Order {order.id}")

            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency="usd",
                description=f"Payment for Order #{order.id}",
                metadata={
                    "order_id": order.id,
                    "external_order_id": ext_order_id,
                    "user_id": user.id,
                },
                # Stripe handles idempotency natively if we provide a key
                idempotency_key=str(uuid.uuid4()),
                automatic_payment_methods={"enabled": True},
            )

            # 3. Audit Trail: Record the attempt with Stripe's ID (pi_...)
            attempt = PaymentAttempt(
                order_id=order.id,
                external_order_id=intent.id,  # Link directly to Stripe ID
                external_customer_id=f"CUST-{user.id}",
                idempotency_key=intent.id,
                amount=order.total_amount,
                currency="USD",
                status=PaymentAttemptStatus.PROCESSING,
                gateway_response=intent,  # Store the Stripe object for debugging
            )
            db.add(attempt)
            db.commit()

            return {
                "client_secret": intent.client_secret,
                "provider_transaction_id": intent.id,
                "status": intent.status.upper(),
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe API Failure: {str(e)}")
            # Record failed attempt locally
            attempt = PaymentAttempt(
                order_id=order.id,
                external_order_id=f"FAILED-{uuid.uuid4().hex[:6]}",
                amount=order.total_amount,
                status=PaymentAttemptStatus.FAILED,
                gateway_response={"error": str(e)},
            )
            db.add(attempt)
            db.commit()
            return None
        except Exception as e:
            logger.critical(
                f"Unexpected Payment System Failure: {str(e)}", exc_info=True
            )
            return None
