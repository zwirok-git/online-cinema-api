from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.movies import (
    Comment,
    CommentLike,
    Director,
    Favorite,
    Genre,
    LikeStatus,
    Movie,
    MovieGenre,
    MovieLike,
    MovieRating,
    Star,
)
from src.models.orders import Order, OrderItem, OrderStatus
from src.schemas.movies import MovieSortField

SORT_COLUMNS = {
    MovieSortField.PRICE: Movie.price,
    MovieSortField.RELEASE_DATE: Movie.year,
    MovieSortField.POPULARITY: Movie.votes,
    MovieSortField.IMDB: Movie.imdb,
}


class MovieRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, movie_id: int) -> Movie | None:
        stmt = select(Movie).where(Movie.id == movie_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(self, movie_id: int) -> Movie | None:
        stmt = (
            select(Movie)
            .where(Movie.id == movie_id)
            .options(
                selectinload(Movie.certification),
                selectinload(Movie.genres),
                selectinload(Movie.stars),
                selectinload(Movie.directors),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_likes(self, movie_id: int, status_: LikeStatus) -> int:
        stmt = select(func.count()).where(MovieLike.movie_id == movie_id, MovieLike.status == status_)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def average_rating(self, movie_id: int) -> float | None:
        stmt = select(func.avg(MovieRating.rating)).where(MovieRating.movie_id == movie_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create_movie(self, movie: Movie) -> bool:
        self.session.add(movie)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return False
        return True

    async def save_movie(self, movie: Movie) -> bool:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return False
        return True

    async def delete_movie(self, movie: Movie) -> None:
        await self.session.delete(movie)
        await self.session.commit()

    async def has_purchases(self, movie_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .where(OrderItem.movie_id == movie_id, Order.status == OrderStatus.PAID)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def get_genres_by_ids(self, ids: list[int]) -> list[Genre]:
        stmt = select(Genre).where(Genre.id.in_(ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_stars_by_ids(self, ids: list[int]) -> list[Star]:
        stmt = select(Star).where(Star.id.in_(ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_directors_by_ids(self, ids: list[int]) -> list[Director]:
        stmt = select(Director).where(Director.id.in_(ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_genre_by_id(self, genre_id: int) -> Genre | None:
        stmt = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_genres_with_movie_count(self):
        stmt = (
            select(Genre, func.count(MovieGenre.movie_id).label("movies_count"))
            .outerjoin(MovieGenre, MovieGenre.genre_id == Genre.id)
            .group_by(Genre.id)
            .order_by(Genre.name)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_favorite(self, movie_id: int, user_id: int) -> Favorite | None:
        stmt = select(Favorite).where(Favorite.movie_id == movie_id, Favorite.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_favorite(self, movie_id: int, user_id: int) -> None:
        self.session.add(Favorite(movie_id=movie_id, user_id=user_id))
        await self.session.commit()

    async def remove_favorite(self, favorite: Favorite) -> None:
        await self.session.delete(favorite)
        await self.session.commit()

    async def get_movie_like(self, movie_id: int, user_id: int) -> MovieLike | None:
        stmt = select(MovieLike).where(MovieLike.movie_id == movie_id, MovieLike.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_movie_like(self, movie_id: int, user_id: int, status_: LikeStatus) -> None:
        existing = await self.get_movie_like(movie_id, user_id)
        if existing is not None:
            existing.status = status_
        else:
            self.session.add(MovieLike(movie_id=movie_id, user_id=user_id, status=status_))
        await self.session.commit()

    async def get_rating(self, movie_id: int, user_id: int) -> MovieRating | None:
        stmt = select(MovieRating).where(MovieRating.movie_id == movie_id, MovieRating.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_rating(self, movie_id: int, user_id: int, rating: int) -> None:
        existing = await self.get_rating(movie_id, user_id)
        if existing is not None:
            existing.rating = rating
        else:
            self.session.add(MovieRating(movie_id=movie_id, user_id=user_id, rating=rating))
        await self.session.commit()

    async def get_comment(self, comment_id: int) -> Comment | None:
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_root_comments(self, movie_id: int) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.movie_id == movie_id, Comment.parent_id.is_(None))
            .options(selectinload(Comment.replies), selectinload(Comment.likes))
            .order_by(Comment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_comment(self, comment: Comment) -> None:
        self.session.add(comment)
        await self.session.flush()

    async def get_comment_like(self, comment_id: int, user_id: int) -> CommentLike | None:
        stmt = select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add_comment_like(self, comment_id: int, user_id: int) -> None:
        self.session.add(CommentLike(comment_id=comment_id, user_id=user_id))

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh_comment(self, comment: Comment) -> None:
        await self.session.refresh(comment, attribute_names=["replies", "likes"])

    async def get_dictionary_item(self, model, item_id: int):
        stmt = select(model).where(model.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_dictionary_item(self, model, name: str):
        item = model(name=name)
        self.session.add(item)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return None, False
        await self.session.refresh(item)
        return item, True

    async def update_dictionary_item(self, item, name: str) -> bool:
        item.name = name
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return False
        await self.session.refresh(item)
        return True

    async def delete_dictionary_item(self, item) -> None:
        await self.session.delete(item)
        await self.session.commit()
