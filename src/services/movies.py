from sqlalchemy.ext.asyncio import AsyncSession

from models.movies import Movie
from repositories.movies import MovieRepository
from schemas.admin_movies import AdminMovieCreateSchema, AdminMovieUpdateSchema


class MovieNotFoundError(Exception):
    pass


class MoviePurchasedError(Exception):
    pass


class RelatedMovieDataError(Exception):
    pass


class MovieService:
    def __init__(self, session: AsyncSession, repository: MovieRepository) -> None:
        self.session = session
        self.repository = repository

    async def list_movies(self, limit: int, offset: int):
        movies = await self.repository.get_all(limit=limit, offset=offset)
        total = await self.repository.get_total()
        return movies, total

    async def get_movie(self, movie_id: int) -> Movie:
        movie = await self.repository.get_by_id(movie_id)
        if movie is None:
            raise MovieNotFoundError("Movie does not exist.")
        return movie

    async def create_movie(self, data: AdminMovieCreateSchema) -> Movie:
        certification = await self.repository.get_certification(data.certification_id)
        if certification is None:
            raise RelatedMovieDataError("Certification does not exist.")

        genres = await self.repository.get_genres_by_ids(data.genre_ids)
        stars = await self.repository.get_stars_by_ids(data.star_ids)
        directors = await self.repository.get_directors_by_ids(data.director_ids)

        movie = Movie(
            name=data.name,
            year=data.year,
            time=data.time,
            imdb=data.imdb,
            votes=data.votes,
            meta_score=data.meta_score,
            gross=data.gross,
            description=data.description,
            price=data.price,
            certification=certification,
            genres=list(genres),
            stars=list(stars),
            directors=list(directors),
        )

        movie = await self.repository.create(movie)
        await self.session.commit()
        return movie

    async def update_movie(self, movie_id: int, data: AdminMovieUpdateSchema) -> Movie:
        movie = await self.get_movie(movie_id)
        update_data = data.model_dump(exclude_unset=True)

        genre_ids = update_data.pop("genre_ids", None)
        star_ids = update_data.pop("star_ids", None)
        director_ids = update_data.pop("director_ids", None)

        certification_id = update_data.pop("certification_id", None)
        if certification_id is not None:
            certification = await self.repository.get_certification(certification_id)
            if certification is None:
                raise RelatedMovieDataError("Certification does not exist.")
            movie.certification = certification

        for field, value in update_data.items():
            setattr(movie, field, value)

        if genre_ids is not None:
            movie.genres = list(await self.repository.get_genres_by_ids(genre_ids))
        if star_ids is not None:
            movie.stars = list(await self.repository.get_stars_by_ids(star_ids))
        if director_ids is not None:
            movie.directors = list(
                await self.repository.get_directors_by_ids(director_ids)
            )

        await self.session.commit()
        return movie

    async def delete_movie(self, movie_id: int) -> None:
        movie = await self.get_movie(movie_id)

        if await self.repository.is_movie_purchased(movie_id):
            raise MoviePurchasedError("Purchased movie cannot be deleted.")

        await self.repository.delete(movie)
        await self.session.commit()
