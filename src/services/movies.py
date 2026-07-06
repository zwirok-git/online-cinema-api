import math

from sqlalchemy import func

from src.exceptions.movies import (
    CertificationNotFoundError,
    CommentNotFoundError,
    DictionaryItemAlreadyExistsError,
    DirectorNotFoundError,
    FavoriteNotFoundError,
    GenreNotFoundError,
    MovieAlreadyExistsError,
    MovieHasPurchasesError,
    MovieNotFoundError,
    StarNotFoundError,
)
from src.models.movies import Comment, LikeStatus, Movie
from src.repositories.movies import MovieRepository
from src.schemas.movies import (
    CommentCreateSchema,
    CommentSchema,
    GenreWithCountSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieFilterParams,
    MovieListItemSchema,
    MovieSortField,
    MovieUpdateSchema,
    PaginatedResponseSchema,
    SortOrder,
)


_ENTITY_LABELS = {
    "genres": "Genre",
    "stars": "Star",
    "directors": "Director",
    "certifications": "Certification",
}
_NOT_FOUND_BY_TABLE = {
    "genres": GenreNotFoundError,
    "stars": StarNotFoundError,
    "directors": DirectorNotFoundError,
    "certifications": CertificationNotFoundError,
}


class MovieService:
    def __init__(self, repo: MovieRepository):
        self.repo = repo

    async def _paginate(
        self, stmt, page: int, per_page: int
    ) -> PaginatedResponseSchema[MovieListItemSchema]:
        db = self.repo.db
        count_stmt = (
            stmt.order_by(None)
            .with_only_columns(func.count())
            .select_from(stmt.subquery())
        )
        total = (await db.execute(count_stmt)).scalar_one()
        rows = (
            (
                await db.execute(
                    stmt.offset((page - 1) * per_page).limit(per_page)
                )
            )
            .scalars()
            .all()
        )
        return PaginatedResponseSchema[MovieListItemSchema](
            items=[MovieListItemSchema.model_validate(r) for r in rows],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=math.ceil(total / per_page) if total else 0,
        )

    async def browse(self, page: int, per_page: int):
        stmt = self.repo.base_query().order_by(Movie.id)
        return await self._paginate(stmt, page, per_page)

    async def filter_movies(
        self, filters: MovieFilterParams, page: int, per_page: int
    ):
        stmt = self.repo.apply_filters(
            self.repo.base_query(), filters
        ).order_by(Movie.id)
        return await self._paginate(stmt, page, per_page)

    async def sort_movies(
        self,
        sort_by: MovieSortField,
        order: SortOrder,
        page: int,
        per_page: int,
    ):
        stmt = self.repo.apply_sort(self.repo.base_query(), sort_by, order)
        return await self._paginate(stmt, page, per_page)

    async def search_movies(self, query: str, page: int, per_page: int):
        stmt = self.repo.apply_search(self.repo.base_query(), query).order_by(
            Movie.id
        )
        return await self._paginate(stmt, page, per_page)

    async def get_detail(self, movie_id: int) -> MovieDetailSchema:
        movie = await self.repo.get_by_id_with_relations(movie_id)
        if movie is None:
            raise MovieNotFoundError(f"Movie id={movie_id} didn't find.")
        likes = await self.repo.count_likes(movie_id, LikeStatus.LIKE)
        dislikes = await self.repo.count_likes(movie_id, LikeStatus.DISLIKE)
        avg = await self.repo.average_rating(movie_id)
        return MovieDetailSchema(
            id=movie.id,
            uuid=movie.uuid,
            name=movie.name,
            year=movie.year,
            time=movie.time,
            imdb=movie.imdb,
            votes=movie.votes,
            meta_score=movie.meta_score,
            gross=movie.gross,
            description=movie.description,
            price=movie.price,
            certification=movie.certification,
            genres=movie.genres,
            stars=movie.stars,
            directors=movie.directors,
            likes_count=likes,
            dislikes_count=dislikes,
            average_rating=round(avg, 2) if avg is not None else None,
        )

    async def create_movie(
        self, payload: MovieCreateSchema
    ) -> MovieDetailSchema:
        movie = Movie(
            **payload.model_dump(
                exclude={"genre_ids", "star_ids", "director_ids"}
            )
        )
        movie.genres = await self.repo.get_genres_by_ids(payload.genre_ids)
        movie.stars = await self.repo.get_stars_by_ids(payload.star_ids)
        movie.directors = await self.repo.get_directors_by_ids(
            payload.director_ids
        )
        if not await self.repo.create_movie(movie):
            raise MovieAlreadyExistsError(
                f"Movie «{payload.name}» ({payload.year},"
                f" {payload.time} min) already exists."
            )
        return await self.get_detail(movie.id)

    async def update_movie(
        self, movie_id: int, payload: MovieUpdateSchema
    ) -> MovieDetailSchema:
        movie = await self.repo.get_by_id(movie_id)
        if movie is None:
            raise MovieNotFoundError(f"Movie id={movie_id} didn't find.")
        data = payload.model_dump(
            exclude_unset=True,
            exclude={"genre_ids", "star_ids", "director_ids"},
        )
        for field, value in data.items():
            setattr(movie, field, value)
        if payload.genre_ids is not None:
            movie.genres = await self.repo.get_genres_by_ids(payload.genre_ids)
        if payload.star_ids is not None:
            movie.stars = await self.repo.get_stars_by_ids(payload.star_ids)
        if payload.director_ids is not None:
            movie.directors = await self.repo.get_directors_by_ids(
                payload.director_ids
            )
        if not await self.repo.save_movie(movie):
            raise MovieAlreadyExistsError(
                f"Movie «{movie.name}» ({movie.year},"
                f" {movie.time} min) already exists."
            )
        return await self.get_detail(movie_id)

    async def delete_movie(self, movie_id: int) -> None:
        movie = await self.repo.get_by_id(movie_id)
        if movie is None:
            raise MovieNotFoundError(f"Movie id={movie_id} didn't find.")
        if await self.repo.has_purchases(movie_id):
            raise MovieHasPurchasesError(
                f"Movie id={movie_id} already sold — deletion is prohibited."
            )
        await self.repo.delete_movie(movie)

    async def list_genres_with_count(self) -> list[GenreWithCountSchema]:
        rows = await self.repo.list_genres_with_movie_count()
        return [
            GenreWithCountSchema(id=g.id, name=g.name, movies_count=c)
            for g, c in rows
        ]

    async def get_movies_by_genre(
        self, genre_id: int, page: int, per_page: int
    ):
        if await self.repo.get_genre_by_id(genre_id) is None:
            raise GenreNotFoundError(f"Genre id={genre_id} didn't find.")
        return await self._paginate(
            self.repo.movies_by_genre_query(genre_id), page, per_page
        )

    async def add_to_favorites(self, movie_id: int, user_id: int) -> None:
        if await self.repo.get_favorite(movie_id, user_id) is not None:
            return
        if await self.repo.get_by_id(movie_id) is None:
            raise MovieNotFoundError(f"Movie id={movie_id} didn't find.")
        await self.repo.add_favorite(movie_id, user_id)

    async def remove_from_favorites(self, movie_id: int, user_id: int) -> None:
        favorite = await self.repo.get_favorite(movie_id, user_id)
        if favorite is None:
            raise FavoriteNotFoundError(
                f"Movie id={movie_id} not in favorites."
            )
        await self.repo.remove_favorite(favorite)

    async def browse_favorites(self, user_id: int, page: int, per_page: int):
        stmt = self.repo.favorites_base_query(user_id).order_by(Movie.id)
        return await self._paginate(stmt, page, per_page)

    async def filter_favorites(
        self,
        user_id: int,
        filters: MovieFilterParams,
        page: int,
        per_page: int,
    ):
        stmt = self.repo.apply_filters(
            self.repo.favorites_base_query(user_id), filters
        ).order_by(Movie.id)
        return await self._paginate(stmt, page, per_page)

    async def sort_favorites(
        self,
        user_id: int,
        sort_by: MovieSortField,
        order: SortOrder,
        page: int,
        per_page: int,
    ):
        stmt = self.repo.apply_sort(
            self.repo.favorites_base_query(user_id), sort_by, order
        )
        return await self._paginate(stmt, page, per_page)

    async def search_favorites(
        self, user_id: int, query: str, page: int, per_page: int
    ):
        stmt = self.repo.apply_search(
            self.repo.favorites_base_query(user_id), query
        ).order_by(Movie.id)
        return await self._paginate(stmt, page, per_page)

    async def like_movie(
        self, movie_id: int, user_id: int, status_: LikeStatus
    ) -> None:
        if await self.repo.get_by_id(movie_id) is None:
            raise MovieNotFoundError(f"Movie id={movie_id} didn't find.")
        await self.repo.upsert_movie_like(movie_id, user_id, status_)

    async def rate_movie(
        self, movie_id: int, user_id: int, rating: int
    ) -> None:
        if await self.repo.get_by_id(movie_id) is None:
            raise MovieNotFoundError(f"Movie id={movie_id} didn't find.")
        await self.repo.upsert_rating(movie_id, user_id, rating)

    def _to_comment_schema(self, comment: Comment) -> CommentSchema:
        return CommentSchema(
            id=comment.id,
            movie_id=comment.movie_id,
            user_id=comment.user_id,
            parent_id=comment.parent_id,
            text=comment.text,
            created_at=comment.created_at,
            replies=[self._to_comment_schema(r) for r in comment.replies],
            likes_count=len(comment.likes),
        )

    async def get_movie_comments(self, movie_id: int) -> list[CommentSchema]:
        comments = await self.repo.get_root_comments(movie_id)
        return [self._to_comment_schema(c) for c in comments]

    async def create_comment(
        self, movie_id: int, user_id: int, payload: CommentCreateSchema
    ) -> CommentSchema:
        parent = None
        if payload.parent_id is not None:
            parent = await self.repo.get_comment(payload.parent_id)
            if parent is None:
                raise CommentNotFoundError(
                    f"Parental comment id={payload.parent_id} didn't find."
                )
        comment = Comment(
            movie_id=movie_id,
            user_id=user_id,
            parent_id=payload.parent_id,
            text=payload.text,
        )
        await self.repo.create_comment(comment)
        if parent is not None and parent.user_id != user_id:
            self.repo.add_notification(parent.user_id, user_id, comment.id)
        await self.repo.commit()
        await self.repo.refresh_comment(comment)
        return self._to_comment_schema(comment)

    async def like_comment(self, comment_id: int, user_id: int) -> None:
        comment = await self.repo.get_comment(comment_id)
        if comment is None:
            raise CommentNotFoundError(f"Comment id={comment_id} didn't find.")
        if await self.repo.get_comment_like(comment_id, user_id) is not None:
            return
        self.repo.add_comment_like(comment_id, user_id)
        if comment.user_id != user_id:
            self.repo.add_notification(comment.user_id, user_id, comment_id)
        await self.repo.commit()

    async def create_dictionary_item(self, model, name: str):
        item, ok = await self.repo.create_dictionary_item(model, name)
        if not ok:
            entity = _ENTITY_LABELS.get(
                model.__tablename__, model.__tablename__
            )
            raise DictionaryItemAlreadyExistsError(
                f"{entity} with name «{name}» already exists."
            )
        return item

    async def update_dictionary_item(self, model, item_id: int, name: str):
        item = await self.repo.get_dictionary_item(model, item_id)
        if item is None:
            raise self._not_found_error(model, item_id)
        if not await self.repo.update_dictionary_item(item, name):
            entity = _ENTITY_LABELS.get(
                model.__tablename__, model.__tablename__
            )
            raise DictionaryItemAlreadyExistsError(
                f"{entity} with name «{name}» already exists."
            )
        return item

    async def delete_dictionary_item(self, model, item_id: int) -> None:
        item = await self.repo.get_dictionary_item(model, item_id)
        if item is None:
            raise self._not_found_error(model, item_id)
        await self.repo.delete_dictionary_item(item)
