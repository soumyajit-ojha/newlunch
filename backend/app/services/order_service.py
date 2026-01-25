import httpx
import uuid
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.orders import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentAttempt,
    PaymentAttemptStatus,
)
from app.models.ecommerce import Cart, CartItem, CartStatus
from app.models.product import Product
from app.models.user import Address

# Structured logging for production monitoring
logger = logging.getLogger("sellphone.orders")


class OrderService:
    @staticmethod
    async def initiate_checkout(
        db: Session, user, address_id: int, cart_item_ids: list[int]
    ):
        """
        Handles the transition from Cart to Order with S2S Intent creation.
        Ensures atomicity: if S2S fails, the cart items are NOT deleted.
        """
        try:
            # 1. DATA VALIDATION
            items = db.query(CartItem).filter(CartItem.id.in_(cart_item_ids)).all()
            if not items:
                raise HTTPException(status_code=400, detail="No valid items selected.")

            address = (
                db.query(Address).filter_by(id=address_id, user_id=user.id).first()
            )
            if not address:
                raise HTTPException(status_code=400, detail="Invalid shipping address.")

            # 2. PRE-CHECK STOCK (Preventing 'Out of Stock' errors mid-transaction)
            for item in items:
                product = db.query(Product).filter_by(id=item.product_id).first()
                if not product or product.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Item {item.product_name_snapshot} is out of stock.",
                    )

            total = sum(i.price_at_addition * i.quantity for i in items)

            # 3. DB TRANSACTION START
            # Create Order record
            order = Order(user_id=user.id, address_id=address_id, total_amount=total)
            db.add(order)
            db.flush()  # Get order.id without committing

            for i in items:
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=i.product_id,
                        quantity=i.quantity,
                        product_name_snapshot=i.product_name_snapshot,
                        price_per_unit=i.price_at_addition,
                    )
                )
                db.delete(i)  # Mark cart items for deletion

            # 4. PREPARE S2S ATTEMPT
            ext_order_id = f"SP-ORD-{order.id}-{uuid.uuid4().hex[:4]}"
            idem_key = str(uuid.uuid4())

            attempt = PaymentAttempt(
                order_id=order.id,
                external_order_id=ext_order_id,
                external_customer_id=f"CUST-{user.id}",
                idempotency_key=idem_key,
                amount=total,
            )
            db.add(attempt)
            db.flush()

            # 5. EXTERNAL S2S CALL (with specific error handling)
            async with httpx.AsyncClient() as client:
                payload = {
                    "external_order_id": ext_order_id,
                    "external_customer_id": attempt.external_customer_id,
                    "amount": total,
                    "currency": "USD",
                    "provider": "STRIPE",
                    "idempotency_key": idem_key,
                }
                headers = {"x-api-key": settings.PAYMENT_GATEWAY_API_KEY}

                try:
                    response = await client.post(
                        f"{settings.PAYMENT_GATEWAY_URL}/payments/initiate",
                        json=payload,
                        headers=headers,
                        timeout=15.0,  # Stop waiting after 15s
                    )
                    response.raise_for_status()  # Raise error for 4xx/5xx responses

                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"S2S Gateway returned error {e.response.status_code}: {e.response.text}"
                    )
                    raise HTTPException(
                        status_code=502, detail="Payment Gateway rejected the request."
                    )
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    logger.error(f"S2S Network Error: {str(e)}")
                    raise HTTPException(
                        status_code=503,
                        detail="Payment Service is currently unreachable.",
                    )

            # 6. COMMIT EVERYTHING IF S2S SUCCESS
            db.commit()
            logger.info(
                f"Checkout initiated: Order {order.id}, ExternalID {ext_order_id}"
            )
            return {"order_id": order.id, "payment_data": response.json()}

        except Exception as e:
            db.rollback()  # CRITICAL: Undo cart deletion and order creation
            if isinstance(e, HTTPException):
                raise e
            logger.critical(f"Unexpected Checkout Failure: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="An internal error occurred.")

    @staticmethod
    def process_payment_webhook(db: Session, external_order_id: str, success: bool):
        """
        Handles the S2S Callback. Includes Idempotency checks to prevent
        duplicate stock deductions if the webhook is sent twice.
        """
        try:
            attempt = (
                db.query(PaymentAttempt)
                .filter_by(external_order_id=external_order_id)
                .first()
            )
            if not attempt:
                logger.warning(
                    f"Webhook received for unknown ExternalID: {external_order_id}"
                )
                return False

            # IDEMPOTENCY CHECK: If already successful, ignore
            if attempt.status == PaymentAttemptStatus.SUCCESS:
                logger.info(
                    f"Duplicate success webhook for {external_order_id}. Ignoring."
                )
                return True

            order = db.query(Order).filter_by(id=attempt.order_id).first()

            if success:
                order.payment_status = PaymentAttemptStatus.SUCCESS
                order.order_status = OrderStatus.CONFIRMED
                attempt.status = PaymentAttemptStatus.SUCCESS

                # STOCK DEDUCTION
                for item in order.order_items:
                    # Use row-level locking to prevent race conditions
                    product = (
                        db.query(Product)
                        .filter_by(id=item.product_id)
                        .with_for_update()
                        .first()
                    )
                    if product:
                        if product.stock >= item.quantity:
                            product.stock -= item.quantity
                        else:
                            logger.error(
                                f"Stock went negative during webhook for Product {product.id}"
                            )
                            # In production, you'd trigger a refund/alert here
            else:
                order.payment_status = PaymentAttemptStatus.FAILED
                order.order_status = OrderStatus.CANCELLED
                attempt.status = PaymentAttemptStatus.FAILED

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Webhook processing error: {str(e)}")
            return False
