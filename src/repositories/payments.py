from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Payment, PaymentItem


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment(self, payment_data: dict) -> Payment:
        payment = Payment(**payment_data)
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: int) -> Payment | None:
        query = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Payment | None:
        query = select(Payment).where(
            Payment.external_payment_id == external_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_payments(self, user_id: int) -> list[Payment]:
        query = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .options(selectinload(Payment.items))
            .order_by(Payment.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PaymentItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment_items(
        self, items_data: list[dict]
    ) -> list[PaymentItem]:
        items = [PaymentItem(**data) for data in items_data]
        self.session.add_all(items)
        await self.session.flush()
        return items
