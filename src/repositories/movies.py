from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.movies import Certification, Director, Genre, Movie, Star
from models.orders import Order, OrderItem, OrderStatus


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, limit: int, offset: int) -> Sequence[Movie]:
        stmt = (
            select(Movie)
            .options(
                selectinload(Movie.genres),
                selectinload(Movie.stars),
                selectinload(Movie.directors),
                selectinload(Movie.certification),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_total(self) -> int:
        result = await self.session.execute(select(func.count(Movie.id)))
        return result.scalar() or 0

    async def get_by_id(self, movie_id: int) -> Movie | None:
        stmt = (
            select(Movie)
            .where(Movie.id == movie_id)
            .options(
                selectinload(Movie.genres),
                selectinload(Movie.stars),
                selectinload(Movie.directors),
                selectinload(Movie.certification),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, movie: Movie) -> Movie:
        self.session.add(movie)
        await self.session.flush()
        await self.session.refresh(movie)
        return movie

    async def delete(self, movie: Movie) -> None:
        await self.session.delete(movie)
        await self.session.flush()

    async def get_certification(
        self, certification_id: int
    ) -> Certification | None:
        return await self.session.get(Certification, certification_id)

    async def get_genres_by_ids(self, ids: list[int]) -> Sequence[Genre]:
        result = await self.session.execute(
            select(Genre).where(Genre.id.in_(ids))
        )
        return result.scalars().all()

    async def get_stars_by_ids(self, ids: list[int]) -> Sequence[Star]:
        result = await self.session.execute(
            select(Star).where(Star.id.in_(ids))
        )
        return result.scalars().all()

    async def get_directors_by_ids(self, ids: list[int]) -> Sequence[Director]:
        result = await self.session.execute(
            select(Director).where(Director.id.in_(ids))
        )
        return result.scalars().all()

    async def is_movie_purchased(self, movie_id: int) -> bool:
        stmt = (
            select(OrderItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(OrderItem.movie_id == movie_id)
            .where(Order.status == OrderStatus.PAID)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
