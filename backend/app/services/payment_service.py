import httpx
import uuid
import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.orders import PaymentAttempt, PaymentAttemptStatus

logger = logging.getLogger("sellphone.payments")


class PaymentService:
    @staticmethod
    async def create_remote_intent(db: Session, order, user):
        """
        SELLPHONE APP: Initiates the request to the S2S Gateway.
        """
        # 1. Generate Unique Strings (Consistently formatted)
        # We include the order.id at the start so the Gateway can easily parse it
        ext_order_id = f"ORD-{order.id}-{uuid.uuid4().hex[:6]}"
        ext_cust_id = f"CUST-{user.id}"
        idem_key = str(uuid.uuid4())

        # 2. Audit Trail: Record the attempt BEFORE calling the gateway
        attempt = PaymentAttempt(
            order_id=order.id,
            external_order_id=ext_order_id,
            external_customer_id=ext_cust_id,
            idempotency_key=idem_key,
            amount=order.total_amount,
            currency="USD",
        )
        db.add(attempt)
        db.commit()

        # 3. Call Remote Payment App
        async with httpx.AsyncClient() as client:
            payload = {
                "external_order_id": ext_order_id,
                "external_customer_id": ext_cust_id,
                "amount": int(order.total_amount),
                "currency": "USD",
                "provider": "STRIPE",
                "idempotency_key": idem_key,
            }
            headers = {"x-api-key": settings.PAYMENT_GATEWAY_API_KEY}

            try:
                logger.info(f"Requesting Payment Intent for Order {order.id}")
                response = await client.post(
                    f"{settings.PAYMENT_GATEWAY_URL}/payment/intent",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                res_data = response.json()
                attempt.gateway_response = res_data

                if response.status_code in [200, 201]:
                    attempt.status = PaymentAttemptStatus.PROCESSING
                    db.commit()
                    return res_data  # Contains Stripe client_secret

                logger.error(f"Gateway rejected request: {response.text}")
                attempt.status = PaymentAttemptStatus.FAILED
                db.commit()
                return None

            except Exception as e:
                logger.error(f"S2S Connection Failed: {str(e)}")
                attempt.status = PaymentAttemptStatus.FAILED
                db.commit()
                return None
