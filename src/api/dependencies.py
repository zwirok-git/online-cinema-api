from typing import Annotated

from fastapi import Depends
from repositories.orders import OrderRepository
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.payments import PaymentRepository
from services.payments import StripePaymentService


async def get_stripe_payment_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> StripePaymentService:
    payment_repo = PaymentRepository(db_session)
    order_repo = OrderRepository(db_session)

    return StripePaymentService(
        payment_repo=payment_repo, order_repo=order_repo
    )
