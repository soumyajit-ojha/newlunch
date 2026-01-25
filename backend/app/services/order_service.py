import stripe
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
from app.models.ecommerce import Cart, CartItem
from app.models.product import Product
from app.models.user import Address

logger = logging.getLogger("sellphone.orders")

# Initialize Stripe with your Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderService:
    @staticmethod
    async def initiate_checkout(
        db: Session, user, address_id: int, cart_item_ids: list[int]
    ):
        """
        DIRECT STRIPE VERSION:
        1. Validates stock.
        2. Creates Order/OrderItems.
        3. Creates Stripe PaymentIntent.
        4. Clears Cart only if Stripe succeeds.
        """
        try:
            # 1. VALIDATION
            items = db.query(CartItem).filter(CartItem.id.in_(cart_item_ids)).all()
            if not items:
                raise HTTPException(status_code=400, detail="No items selected.")

            address = (
                db.query(Address).filter_by(id=address_id, user_id=user.id).first()
            )
            if not address:
                raise HTTPException(status_code=400, detail="Invalid address.")

            # 2. PRE-CHECK STOCK
            for item in items:
                product = db.query(Product).filter_by(id=item.product_id).first()
                if not product or product.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Stock for {item.product_name_snapshot} is insufficient.",
                    )

            total = sum(i.price_at_addition * i.quantity for i in items)

            # 3. CREATE ORDER RECORD (Status: INITIATED)
            order = Order(user_id=user.id, address_id=address_id, total_amount=total)
            db.add(order)
            db.flush()

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
                db.delete(i)  # Prepare cart for clearing

            # 4. DIRECT CALL TO STRIPE API
            try:
                # Stripe expects amount in cents (integer)
                amount_in_cents = int(total * 100)

                intent = stripe.PaymentIntent.create(
                    amount=amount_in_cents,
                    currency="usd",
                    metadata={"order_id": order.id, "user_email": user.email},
                    automatic_payment_methods={"enabled": True},
                )
            except stripe.error.StripeError as e:
                logger.error(f"Stripe Error: {str(e)}")
                raise HTTPException(
                    status_code=502, detail="Could not initialize payment with Stripe."
                )

            # 5. CREATE ATTEMPT LOG
            attempt = PaymentAttempt(
                order_id=order.id,
                external_order_id=intent.id,  # Stripe's ID (pi_...)
                external_customer_id=f"CUST-{user.id}",
                idempotency_key=intent.id,  # Use Stripe's ID to prevent duplicate processing
                amount=total,
                status=PaymentAttemptStatus.PROCESSING,
            )
            db.add(attempt)

            # Link Stripe session to order
            order.payment_session_id = intent.id

            db.commit()  # Save everything
            logger.info(
                f"Checkout initiated for Order {order.id}. Stripe Intent: {intent.id}"
            )

            return {
                "order_id": order.id,
                "client_secret": intent.client_secret,
                "external_order_id": intent.id,
            }

        except Exception as e:
            db.rollback()
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Checkout Logic Failure: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Transaction failed.")

    @staticmethod
    def finalize_payment_success(db: Session, stripe_intent_id: str):
        """
        CORE FULFILLMENT LOGIC:
        Triggered by Webhook. Ensures stock deduction happens exactly once.
        """
        try:
            # 1. Find the Attempt
            attempt = (
                db.query(PaymentAttempt)
                .filter_by(external_order_id=stripe_intent_id)
                .first()
            )
            if not attempt:
                logger.error(f"Payment success for unknown intent: {stripe_intent_id}")
                return False

            if attempt.status == PaymentAttemptStatus.SUCCESS:
                return True  # Idempotency: Already processed

            # 2. Find and Lock the Order
            order = db.query(Order).filter(Order.id == attempt.order_id).first()

            # 3. ATOMIC STOCK DEDUCTION
            for item in order.order_items:
                product = (
                    db.query(Product)
                    .filter(Product.id == item.product_id)
                    .with_for_update()
                    .first()
                )
                if product:
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                    else:
                        logger.critical(
                            f"OVERSELL ALERT: Order {order.id} paid but Product {product.id} out of stock!"
                        )

            # 4. UPDATE STATUSES
            order.order_status = OrderStatus.CONFIRMED
            order.payment_status = PaymentAttemptStatus.SUCCESS
            attempt.status = PaymentAttemptStatus.SUCCESS

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Fulfillment Failure: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def handle_payment_failure(db: Session, stripe_intent_id: str):
        """Cancels the order record if payment is declined"""
        attempt = (
            db.query(PaymentAttempt)
            .filter_by(external_order_id=stripe_intent_id)
            .first()
        )
        if attempt:
            order = db.query(Order).filter(Order.id == attempt.order_id).first()
            if order:
                order.order_status = OrderStatus.CANCELLED
                order.payment_status = PaymentAttemptStatus.FAILED
                attempt.status = PaymentAttemptStatus.FAILED
                db.commit()

    @staticmethod
    def process_payment_webhook(db: Session, external_order_id: str, success: bool):
        """Dispatches to the appropriate handler based on payment status."""
        if success:
            return OrderService.finalize_payment_success(db, external_order_id)
        else:
            OrderService.handle_payment_failure(db, external_order_id)
            return True
