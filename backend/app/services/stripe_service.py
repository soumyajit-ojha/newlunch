import stripe
import logging
from app.core.config import settings

logger = logging.getLogger("sellphone.stripe")
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    def create_payment_intent(amount: float, order_id: int, user_email: str):
        """
        Creates a PaymentIntent on Stripe.
        We store the order_id in metadata to link the webhook back to our DB.
        """
        try:
            # Stripe expects amount in cents/paise (int)
            amount_in_cents = int(amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency="usd",
                metadata={"order_id": order_id, "user_email": user_email},
                automatic_payment_methods={"enabled": True},
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Intent Error: {str(e)}")
            raise Exception("Payment provider is currently unavailable.")

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str):
        """
        Verifies that the webhook request came from Stripe and hasn't been tampered with.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook Signature Verification Failed: {str(e)}")
            return None
