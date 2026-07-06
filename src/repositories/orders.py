from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movies import Movie
from models.orders import Order, OrderItem, OrderStatus


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_movies_by_ids(self, movie_ids: list[int]) -> list[Movie]:
        result = await self.db.execute(
            select(Movie).where(Movie.id.in_(movie_ids))
        )
        return list(result.scalars().all())

    async def get_purchased_movie_ids(self, user_id: int) -> set[int]:
        result = await self.db.execute(
            select(OrderItem.movie_id)
            .join(Order)
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatus.PAID,
            )
        )
        return set(result.scalars().all())

    async def get_pending_movie_ids(self, user_id: int) -> set[int]:
        result = await self.db.execute(
            select(OrderItem.movie_id)
            .join(Order)
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatus.PENDING,
            )
        )
        return set(result.scalars().all())

    async def create_order(self, user_id: int, movies: list[Movie]) -> Order:
        order = Order(
            user_id=user_id,
            total_amount=sum(
                (movie.price for movie in movies), Decimal("0.00")
            ),
            items=[
                OrderItem(movie_id=movie.id, price_at_order=movie.price)
                for movie in movies
            ],
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_user_orders(self, user_id: int) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_order_by_id(self, order_id: int) -> Order | None:
        return await self.db.get(Order, order_id)

    async def update_status(self, order: Order, status: OrderStatus) -> Order:
        order.status = status
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_all_orders(
        self,
        user_id: int | None = None,
        status: OrderStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc())
        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Order.status == status)
        if date_from is not None:
            stmt = stmt.where(Order.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Order.created_at <= date_to)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
