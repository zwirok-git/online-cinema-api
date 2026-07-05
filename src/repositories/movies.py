from typing import Any

from sqlalchemy import func, or_, select, Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import Base
from src.models.movies import (
    CommentLike,
    Comment,
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
from src.schemas.movies import MovieFilterParams, MovieSortField, SortOrder

SORT_COLUMNS = {
    MovieSortField.PRICE: Movie.price,
    MovieSortField.RELEASE_DATE: Movie.year,
    MovieSortField.POPULARITY: Movie.votes,
    MovieSortField.IMDB: Movie.imdb,
}



def base_query():
    return select(Movie)


def apply_filters(stmt, filters: MovieFilterParams):
    if filters.year is not None:
        stmt = stmt.where(Movie.year == filters.year)
    if filters.year_from is not None:
        stmt = stmt.where(Movie.year >= filters.year_from)
    if filters.year_to is not None:
        stmt = stmt.where(Movie.year <= filters.year_to)
    if filters.imdb_from is not None:
        stmt = stmt.where(Movie.imdb >= filters.imdb_from)
    if filters.imdb_to is not None:
        stmt = stmt.where(Movie.imdb <= filters.imdb_to)
    if filters.genre_id is not None:
        stmt = stmt.join(Movie.genres).where(Genre.id == filters.genre_id)
    return stmt


def apply_sort(stmt, sort_by: MovieSortField, order: SortOrder):
    column = SORT_COLUMNS[sort_by]
    return stmt.order_by(column.desc() if order == SortOrder.DESC else column.asc())


def apply_search(stmt, query: str):
    pattern = f"%{query}%"
    return (
        stmt.outerjoin(Movie.stars)
        .outerjoin(Movie.directors)
        .where(
            or_(
                Movie.name.ilike(pattern),
                Movie.description.ilike(pattern),
                Star.name.ilike(pattern),
                Director.name.ilike(pattern),
            )
        )
        .distinct()
    )


async def get_by_id(db: AsyncSession, movie_id: int) -> Movie | None:
    return await db.get(Movie, movie_id)


async def get_by_id_with_relations(db: AsyncSession, movie_id: int) -> Movie | None:
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
    return (await db.execute(stmt)).scalar_one_or_none()


async def count_likes(db: AsyncSession, movie_id: int, status_: LikeStatus) -> int:
    stmt = select(func.count()).where(MovieLike.movie_id == movie_id, MovieLike.status == status_)
    return (await db.execute(stmt)).scalar_one()


async def average_rating(db: AsyncSession, movie_id: int) -> float | None:
    stmt = select(func.avg(MovieRating.rating)).where(MovieRating.movie_id == movie_id)
    return (await db.execute(stmt)).scalar_one()


async def create_movie(db: AsyncSession, movie: Movie) -> bool:
    db.add(movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return False
    return True


async def save_movie(db: AsyncSession, movie: Movie) -> bool:
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return False
    return True


async def delete_movie(db: AsyncSession, movie: Movie) -> None:
    await db.delete(movie)
    await db.commit()


async def has_purchases(db: AsyncSession, movie_id: int) -> bool:
    stmt = (
        select(func.count())
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .where(OrderItem.movie_id == movie_id, Order.status == OrderStatus.PAID)
    )
    count = (await db.execute(stmt)).scalar_one()
    return count > 0


async def get_genres_by_ids(db: AsyncSession, ids: list[int]) -> list[Genre]:
    return list((await db.execute(select(Genre).where(Genre.id.in_(ids)))).scalars().all())


async def get_stars_by_ids(db: AsyncSession, ids: list[int]) -> list[Star]:
    return list((await db.execute(select(Star).where(Star.id.in_(ids)))).scalars().all())


async def get_directors_by_ids(db: AsyncSession, ids: list[int]) -> list[Director]:
    return list((await db.execute(select(Director).where(Director.id.in_(ids)))).scalars().all())


async def get_genre_by_id(db: AsyncSession, genre_id: int) -> Genre | None:
    return await db.get(Genre, genre_id)


async def list_genres_with_movie_count(db: AsyncSession) -> list[Row[tuple[Any, Any]]]:
    stmt = (
        select(Genre, func.count(MovieGenre.movie_id).label("movies_count"))
        .outerjoin(MovieGenre, MovieGenre.genre_id == Genre.id)
        .group_by(Genre.id)
        .order_by(Genre.name)
    )
    return list((await db.execute(stmt)).all())


def movies_by_genre_query(genre_id: int):
    return select(Movie).join(Movie.genres).where(Genre.id == genre_id).order_by(Movie.id)


async def get_favorite(db: AsyncSession, *, movie_id: int, user_id: int) -> Favorite | None:
    stmt = select(Favorite).where(Favorite.movie_id == movie_id, Favorite.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def add_favorite(db: AsyncSession, *, movie_id: int, user_id: int) -> None:
    db.add(Favorite(movie_id=movie_id, user_id=user_id))
    await db.commit()


async def remove_favorite(db: AsyncSession, favorite: Favorite) -> None:
    await db.delete(favorite)
    await db.commit()


def favorites_base_query(user_id: int):
    return select(Movie).join(Favorite, Favorite.movie_id == Movie.id).where(Favorite.user_id == user_id)


async def get_movie_like(db: AsyncSession, *, movie_id: int, user_id: int) -> MovieLike | None:
    stmt = select(MovieLike).where(MovieLike.movie_id == movie_id, MovieLike.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def upsert_movie_like(db: AsyncSession, *, movie_id: int, user_id: int, status_: LikeStatus) -> None:
    existing = await get_movie_like(db, movie_id=movie_id, user_id=user_id)
    if existing is not None:
        existing.status = status_
    else:
        db.add(MovieLike(movie_id=movie_id, user_id=user_id, status=status_))
    await db.commit()


async def get_rating(db: AsyncSession, *, movie_id: int, user_id: int) -> MovieRating | None:
    stmt = select(MovieRating).where(MovieRating.movie_id == movie_id, MovieRating.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def upsert_rating(db: AsyncSession, *, movie_id: int, user_id: int, rating: int) -> None:
    existing = await get_rating(db, movie_id=movie_id, user_id=user_id)
    if existing is not None:
        existing.rating = rating
    else:
        db.add(MovieRating(movie_id=movie_id, user_id=user_id, rating=rating))
    await db.commit()


async def get_comment(db: AsyncSession, comment_id: int) -> Comment | None:
    return await db.get(Comment, comment_id)


async def get_root_comments(db: AsyncSession, movie_id: int) -> list[Comment]:
    stmt = (
        select(Comment)
        .where(Comment.movie_id == movie_id, Comment.parent_id.is_(None))
        .options(selectinload(Comment.replies), selectinload(Comment.likes))
        .order_by(Comment.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def create_comment(db: AsyncSession, comment: Comment) -> None:
    db.add(comment)
    await db.flush()


async def get_comment_like(db: AsyncSession, *, comment_id: int, user_id: int) -> CommentLike | None:
    stmt = select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


def add_comment_like(db: AsyncSession, *, comment_id: int, user_id: int) -> None:
    db.add(CommentLike(comment_id=comment_id, user_id=user_id))


async def commit(db: AsyncSession) -> None:
    await db.commit()


async def refresh_comment(db: AsyncSession, comment: Comment) -> None:
    await db.refresh(comment, attribute_names=["replies", "likes"])


async def get_dictionary_item(db: AsyncSession, model: type[Base], item_id: int):
    return await db.get(model, item_id)


async def list_dictionary_items(db: AsyncSession, model: type[Base]):
    return list((await db.execute(select(model))).scalars().all())


async def create_dictionary_item(db: AsyncSession, model: type[Base], name: str):
    item = model(name=name)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return None, False
    await db.refresh(item)
    return item, True


async def update_dictionary_item(db: AsyncSession, item, name: str) -> bool:
    item.name = name
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return False
    await db.refresh(item)
    return True


async def delete_dictionary_item(db: AsyncSession, item) -> None:
    await db.delete(item)
    await db.commit()
