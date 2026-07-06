import contextlib
from datetime import datetime
from decimal import Decimal

import stripe
from fastapi import HTTPException, status

from core.config import settings
from exceptions.orders import OrderNotFoundError, OrderNotPayableError
from exceptions.payments import (
    InvalidOrderStatusException,
    OrderAccessDeniedException,
    OrderNotFoundException,
)
from models import Payment
from models.orders import OrderStatus
from repositories.orders import OrderRepository
from repositories.payments import PaymentRepository
from services.orders import OrderService
from services.payments.base_payment import IPaymentService


class StripePaymentService(IPaymentService):
    def __init__(
        self,
        payment_repo: PaymentRepository,
        order_repo: OrderRepository,
    ):
        self.payment_repo = payment_repo
        self.order_repo = order_repo
        self.client = stripe.StripeClient(settings.STRIPE_SECRET_KEY)

    async def create_checkout_session(
        self, order_id: int, user_id: int
    ) -> str:
        order = await self.order_repo.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException(f"Order #{order_id} not found")

        if order.user_id != user_id:
            raise OrderAccessDeniedException("Access denied for this order")

        if order.status != OrderStatus.PENDING:
            raise InvalidOrderStatusException(
                f"Order cannot be paid. Current status: {order.status}"
            )

        total_amount = order.total_amount or Decimal("0.00")
        stripe_amount = int(total_amount * Decimal("100"))

        try:
            checkout_session = (
                await self.client.checkout.sessions.create_async(
                    params={
                        "payment_method_types": ["card"],
                        "line_items": [
                            {
                                "price_data": {
                                    "currency": "usd",
                                    "product_data": {
                                        "name": f"Payment for "
                                        f"Order #{order.id}",
                                    },
                                    "unit_amount": stripe_amount,
                                },
                                "quantity": 1,
                            }
                        ],
                        "mode": "payment",
                        "success_url": (
                            f"{settings.BASE_URL}/success"
                            "?session_id={CHECKOUT_SESSION_ID}"
                        ),
                        "cancel_url": f"{settings.BASE_URL}/cancel",
                        "metadata": {
                            "order_id": str(order.id),
                            "user_id": str(user_id),
                        },
                    }
                )
            )

            if not checkout_session.url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Stripe did not provide a checkout URL.",
                )

            payment_data = {
                "user_id": user_id,
                "order_id": order.id,
                "amount": order.total_amount,
                "status": "pending",
                "external_payment_id": checkout_session.id,
            }
            await self.payment_repo.create_payment(payment_data)

            return str(checkout_session.url)

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe session generation failed",
            ) from None

    async def handle_webhook(self, payload: bytes, sig_header: str) -> bool:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload",
            ) from None
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            ) from None

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            order_id = int(session["metadata"]["order_id"])
            external_payment_id = session["id"]
            payment = await self.payment_repo.get_by_external_id(
                external_payment_id
            )
            if payment:
                await self.payment_repo.update_payment(
                    payment.id, {"status": "paid"}
                )

            with contextlib.suppress(OrderNotFoundError, OrderNotPayableError):
                await OrderService(repo=self.order_repo).mark_paid(order_id)

        return True

    async def get_user_history(self, user_id: int) -> list[Payment]:
        return await self.payment_repo.get_user_payments(user_id=user_id)

    async def get_all_payments_for_admin(
        self,
        user_id: int | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Payment]:
        return await self.payment_repo.get_all_payments_admin(
            user_id=user_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )
