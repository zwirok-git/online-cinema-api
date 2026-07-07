from datetime import datetime

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
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Payment | None:
        stmt = select(Payment).where(
            Payment.external_payment_id == external_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_payments(self, user_id: int) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .options(selectinload(Payment.items))
            .order_by(Payment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_payment(
        self, payment_id: int, update_data: dict
    ) -> Payment | None:
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None

        for key, value in update_data.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        await self.session.flush()
        return payment

    async def get_all_payments_admin(
        self,
        user_id: int | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Payment]:
        stmt = select(Payment).order_by(Payment.created_at.desc())

        if user_id is not None:
            stmt = stmt.where(Payment.user_id == user_id)

        if status is not None:
            stmt = stmt.where(Payment.status == status)

        if start_date is not None:
            stmt = stmt.where(Payment.created_at >= start_date)

        if end_date is not None:
            stmt = stmt.where(Payment.created_at <= end_date)

        result = await self.session.execute(stmt)
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
