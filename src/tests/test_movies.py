from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from exceptions.movies import (
    CommentNotFoundError,
    DictionaryItemAlreadyExistsError,
    GenreNotFoundError,
    MovieAlreadyExistsError,
    MovieNotFoundError,
)
from schemas.movies import (
    CommentCreateSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieFilterParams,
    MovieSearchParams,
    CommentSchema,
    MovieListItemSchema,
    PaginatedResponseSchema
)
from services.movies import MovieService
from models.movies import (
    Certification,
    Comment,
    Director,
    Genre,
    LikeStatus,
    Movie,
    Star,
)
from models.orders import Order, OrderItem, OrderStatus
from models.users import UserGroupEnum, UserGroupModel, UserModel
from repositories.movies import MovieRepository


class FakeMovieRepository:
    def __init__(
        self,
        movie=None,
        genre=None,
        favorite=None,
        comment=None,
        comment_like=None,
        dictionary_item=None,
        create_ok=True,
        save_ok=True,
        dict_create_ok=True,
        dict_update_ok=True,
    ):
        self.movie = movie
        self.genre = genre
        self.favorite = favorite
        self.comment = comment
        self.comment_like = comment_like
        self.dictionary_item = dictionary_item
        self._create_ok = create_ok
        self._save_ok = save_ok
        self._dict_create_ok = dict_create_ok
        self._dict_update_ok = dict_update_ok

        self.favorited = False
        self.liked_status = None
        self.rated = None
        self.created_comment = None
        self.comment_liked = False
        self.deleted_item = False

    async def get_by_id(self, movie_id):
        return self.movie

    async def get_by_id_with_relations(self, movie_id):
        return self.movie

    async def count_likes(self, movie_id, status_):
        return 0

    async def average_rating(self, movie_id):
        return None

    async def get_genres_by_ids(self, ids):
        return []

    async def get_stars_by_ids(self, ids):
        return []

    async def get_directors_by_ids(self, ids):
        return []

    async def create_movie(self, movie):
        return self._create_ok

    async def save_movie(self, movie):
        return self._save_ok

    async def get_genre_by_id(self, genre_id):
        return self.genre

    async def get_favorite(self, movie_id, user_id):
        return self.favorite

    async def add_favorite(self, movie_id, user_id):
        self.favorited = True

    async def upsert_movie_like(self, movie_id, user_id, status_):
        self.liked_status = status_

    async def upsert_rating(self, movie_id, user_id, rating):
        self.rated = rating

    async def get_comment(self, comment_id):
        return self.comment

    async def create_comment(self, comment):
        self.created_comment = comment

    async def commit(self):
        pass

    async def refresh_comment(self, comment):
        comment.created_at = comment.created_at or datetime.now(timezone.utc)
        comment.id = comment.id or 1

    async def get_comment_like(self, comment_id, user_id):
        return self.comment_like

    def add_comment_like(self, comment_id, user_id):
        self.comment_liked = True

    async def get_dictionary_item(self, model, item_id):
        return self.dictionary_item

    async def create_dictionary_item(self, model, name):
        if not self._dict_create_ok:
            return None, False
        return self.dictionary_item, True

    async def update_dictionary_item(self, item, name):
        return self._dict_update_ok

    async def delete_dictionary_item(self, item):
        self.deleted_item = True


def _movie_with_relations(**overrides):
    defaults = dict(
        id=1,
        name="Dune",
        price=None,
        certification=Certification(id=1, name="R"),
        genres=[],
        stars=[],
        directors=[],
    )
    defaults.update(overrides)
    return Movie(**defaults)


@pytest.mark.asyncio
async def test_update_movie_raises_when_missing():
    service = MovieService(repo=FakeMovieRepository(movie=None))

    with pytest.raises(MovieNotFoundError):
        await service.update_movie(1, MovieUpdateSchema())


@pytest.mark.asyncio
async def test_update_movie_raises_on_duplicate():
    movie = Movie(id=1, name="Dune", year=2021, time=155, price=None)
    service = MovieService(repo=FakeMovieRepository(movie=movie, save_ok=False))

    with pytest.raises(MovieAlreadyExistsError):
        await service.update_movie(1, MovieUpdateSchema(name="New Name"))


@pytest.mark.asyncio
async def test_add_to_favorites_returns_early_when_already_favorited():
    repo = FakeMovieRepository(favorite=object(), movie=None)
    service = MovieService(repo=repo)

    await service.add_to_favorites(movie_id=1, user_id=1)

    assert repo.favorited is False


@pytest.mark.asyncio
async def test_add_to_favorites_success():
    movie = Movie(id=1, name="Dune", price=None)
    repo = FakeMovieRepository(favorite=None, movie=movie)
    service = MovieService(repo=repo)

    await service.add_to_favorites(movie_id=1, user_id=1)

    assert repo.favorited is True


@pytest.mark.asyncio
async def test_like_movie_success():
    movie = Movie(id=1, name="Dune", price=None)
    repo = FakeMovieRepository(movie=movie)
    service = MovieService(repo=repo)

    await service.like_movie(movie_id=1, user_id=1, status_=LikeStatus.LIKE)

    assert repo.liked_status == LikeStatus.LIKE


@pytest.mark.asyncio
async def test_rate_movie_raises_when_movie_missing():
    service = MovieService(repo=FakeMovieRepository(movie=None))

    with pytest.raises(MovieNotFoundError):
        await service.rate_movie(movie_id=1, user_id=1, rating=8)


@pytest.mark.asyncio
async def test_rate_movie_success():
    movie = Movie(id=1, name="Dune", price=None)
    repo = FakeMovieRepository(movie=movie)
    service = MovieService(repo=repo)

    await service.rate_movie(movie_id=1, user_id=1, rating=9)

    assert repo.rated == 9


@pytest.mark.asyncio
async def test_get_movies_by_genre_raises_when_genre_missing():
    service = MovieService(repo=FakeMovieRepository(genre=None))

    with pytest.raises(GenreNotFoundError):
        await service.get_movies_by_genre(genre_id=999, page=1, per_page=20)


@pytest.mark.asyncio
async def test_create_comment_raises_when_parent_missing():
    service = MovieService(repo=FakeMovieRepository(comment=None))
    payload = CommentCreateSchema(text="hi", parent_id=123)

    with pytest.raises(CommentNotFoundError):
        await service.create_comment(movie_id=1, user_id=1, payload=payload)


@pytest.mark.asyncio
async def test_create_comment_success_without_parent():
    repo = FakeMovieRepository()
    service = MovieService(repo=repo)
    payload = CommentCreateSchema(text="great movie", parent_id=None)

    result = await service.create_comment(movie_id=1, user_id=1, payload=payload)

    assert result.text == "great movie"
    assert result.replies == []
    assert repo.created_comment is not None


@pytest.mark.asyncio
async def test_like_comment_raises_when_comment_missing():
    service = MovieService(repo=FakeMovieRepository(comment=None))

    with pytest.raises(CommentNotFoundError):
        await service.like_comment(comment_id=1, user_id=1)


@pytest.mark.asyncio
async def test_like_comment_returns_early_when_already_liked():
    comment = Comment(id=1, movie_id=1, user_id=2, text="x")
    repo = FakeMovieRepository(comment=comment, comment_like=object())
    service = MovieService(repo=repo)

    await service.like_comment(comment_id=1, user_id=1)

    assert repo.comment_liked is False


@pytest.mark.asyncio
async def test_like_comment_success():
    comment = Comment(id=1, movie_id=1, user_id=2, text="x")
    repo = FakeMovieRepository(comment=comment, comment_like=None)
    service = MovieService(repo=repo)

    await service.like_comment(comment_id=1, user_id=1)

    assert repo.comment_liked is True


@pytest.mark.asyncio
async def test_create_dictionary_item_raises_on_duplicate():
    service = MovieService(repo=FakeMovieRepository(dict_create_ok=False))

    with pytest.raises(DictionaryItemAlreadyExistsError):
        await service.create_dictionary_item(Genre, "Drama")


@pytest.mark.asyncio
async def test_update_dictionary_item_raises_when_missing():
    service = MovieService(repo=FakeMovieRepository(dictionary_item=None))

    with pytest.raises(GenreNotFoundError):
        await service.update_dictionary_item(Genre, 999, "New Name")


@pytest.mark.asyncio
async def test_update_dictionary_item_raises_on_duplicate():
    genre = Genre(id=1, name="Drama")
    service = MovieService(
        repo=FakeMovieRepository(dictionary_item=genre, dict_update_ok=False)
    )

    with pytest.raises(DictionaryItemAlreadyExistsError):
        await service.update_dictionary_item(Genre, 1, "Comedy")


@pytest.mark.asyncio
async def test_delete_dictionary_item_raises_when_missing():
    service = MovieService(repo=FakeMovieRepository(dictionary_item=None))

    with pytest.raises(GenreNotFoundError):
        await service.delete_dictionary_item(Genre, 999)


@pytest.mark.asyncio
async def test_delete_dictionary_item_success():
    genre = Genre(id=1, name="Drama")
    repo = FakeMovieRepository(dictionary_item=genre)
    service = MovieService(repo=repo)

    await service.delete_dictionary_item(Genre, 1)

    assert repo.deleted_item is True


def _valid_movie_kwargs(**overrides):
    defaults = dict(
        name="Dune",
        year=2021,
        time=155,
        imdb=8.0,
        votes=100,
        description="A movie",
        certification_id=1,
    )
    defaults.update(overrides)
    return defaults


def test_movie_create_schema_accepts_valid_payload():
    movie = MovieCreateSchema(**_valid_movie_kwargs())
    assert movie.genre_ids == []
    assert movie.star_ids == []
    assert movie.director_ids == []


def test_movie_create_schema_rejects_negative_time():
    with pytest.raises(ValidationError):
        MovieCreateSchema(**_valid_movie_kwargs(time=0))


def test_movie_create_schema_rejects_imdb_out_of_range():
    with pytest.raises(ValidationError):
        MovieCreateSchema(**_valid_movie_kwargs(imdb=10.5))


def test_movie_create_schema_rejects_negative_votes():
    with pytest.raises(ValidationError):
        MovieCreateSchema(**_valid_movie_kwargs(votes=-1))


def test_movie_create_schema_rejects_negative_price():
    with pytest.raises(ValidationError):
        MovieCreateSchema(**_valid_movie_kwargs(price=-5))


def test_movie_create_schema_rejects_meta_score_out_of_range():
    with pytest.raises(ValidationError):
        MovieCreateSchema(**_valid_movie_kwargs(meta_score=150))


def test_movie_filter_params_valid_imdb_range():
    filters = MovieFilterParams(imdb_from=5.0, imdb_to=8.0)
    assert filters.imdb_from == 5.0
    assert filters.imdb_to == 8.0


def test_movie_filter_params_rejects_inverted_imdb_range():
    with pytest.raises(ValidationError):
        MovieFilterParams(imdb_from=8.0, imdb_to=5.0)


def test_movie_filter_params_allows_missing_imdb_bounds():
    filters = MovieFilterParams()
    assert filters.imdb_from is None
    assert filters.imdb_to is None


def test_movie_search_params_rejects_empty_query():
    with pytest.raises(ValidationError):
        MovieSearchParams(query="")


def test_movie_search_params_accepts_valid_query():
    params = MovieSearchParams(query="dune")
    assert params.query == "dune"


def test_comment_create_schema_rejects_empty_text():
    with pytest.raises(ValidationError):
        CommentCreateSchema(text="")


def test_comment_create_schema_rejects_text_too_long():
    with pytest.raises(ValidationError):
        CommentCreateSchema(text="x" * 2001)


def test_comment_create_schema_accepts_valid_text_without_parent():
    comment = CommentCreateSchema(text="Great movie!")
    assert comment.parent_id is None


def test_comment_schema_supports_nested_replies():
    reply = CommentSchema(
        id=2,
        movie_id=1,
        user_id=2,
        parent_id=1,
        text="I agree",
        created_at=datetime.now(timezone.utc),
    )
    comment = CommentSchema(
        id=1,
        movie_id=1,
        user_id=1,
        parent_id=None,
        text="Great movie!",
        created_at=datetime.now(timezone.utc),
        replies=[reply],
    )
    assert len(comment.replies) == 1
    assert comment.replies[0].text == "I agree"


def test_paginated_response_schema_computes_generic_items():
    item = MovieListItemSchema(
        id=1, uuid="12345678-1234-5678-1234-567812345678",
        name="Dune", year=2021, imdb=8.0, price=None,
    )
    page = PaginatedResponseSchema[MovieListItemSchema](
        items=[item], total=1, page=1, per_page=20, total_pages=1
    )
    assert page.items[0].name == "Dune"
    assert page.total_pages == 1


@pytest.fixture
async def user_group_id(db_session):
    result = await db_session.execute(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.USER
        )
    )
    return result.scalar_one().id



@pytest.fixture
async def user_id(db_session, user_group_id):
    user = UserModel(
        email="repo@test.com",
        hashed_password="x",
        is_active=True,
        group_id=user_group_id,
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def certification_id(db_session):
    cert = Certification(name="PG-13")
    db_session.add(cert)
    await db_session.flush()
    return cert.id


@pytest.fixture
def repo(db_session):
    return MovieRepository(db_session)


@pytest.fixture
async def movie_id(db_session, certification_id):
    movie = Movie(
        name="Dune",
        year=2021,
        time=155,
        imdb=8.0,
        votes=100,
        description="A movie",
        price=Decimal("9.99"),
        certification_id=certification_id,
    )
    db_session.add(movie)
    await db_session.flush()
    return movie.id


@pytest.mark.asyncio
async def test_create_movie_success_and_duplicate(repo, certification_id):
    movie = Movie(
        name="Arrival", year=2016, time=116, imdb=7.9, votes=50,
        description="d", price=Decimal("5.00"),
        certification_id=certification_id,
    )
    assert await repo.create_movie(movie) is True

    duplicate = Movie(
        name="Arrival", year=2016, time=116, imdb=7.9, votes=50,
        description="d", price=Decimal("5.00"),
        certification_id=certification_id,
    )
    assert await repo.create_movie(duplicate) is False


@pytest.mark.asyncio
async def test_get_by_id_found_and_missing(repo, movie_id):
    assert (await repo.get_by_id(movie_id)).id == movie_id
    assert await repo.get_by_id(999999) is None


@pytest.mark.asyncio
async def test_get_by_id_with_relations(repo, movie_id):
    movie = await repo.get_by_id_with_relations(movie_id)
    assert movie is not None
    assert movie.certification is not None
    assert movie.genres == []


@pytest.mark.asyncio
async def test_delete_movie(repo, movie_id):
    movie = await repo.get_by_id(movie_id)
    await repo.delete_movie(movie)
    assert await repo.get_by_id(movie_id) is None


@pytest.mark.asyncio
async def test_has_purchases_true_and_false(
        repo, db_session, movie_id, user_id
):
    assert await repo.has_purchases(movie_id) is False

    order = Order(user_id=user_id, status=OrderStatus.PAID)
    db_session.add(order)
    await db_session.flush()
    db_session.add(
        OrderItem(
            order_id=order.id, movie_id=movie_id, price_at_order=Decimal("9.99")
        )
    )
    await db_session.flush()

    assert await repo.has_purchases(movie_id) is True


@pytest.mark.asyncio
async def test_get_genres_stars_directors_by_ids(repo, db_session):
    genre = Genre(name="Sci-Fi")
    star = Star(name="Timothee Chalamet")
    director = Director(name="Denis Villeneuve")
    db_session.add_all([genre, star, director])
    await db_session.flush()

    genres = await repo.get_genres_by_ids([genre.id])
    stars = await repo.get_stars_by_ids([star.id])
    directors = await repo.get_directors_by_ids([director.id])

    assert [g.id for g in genres] == [genre.id]
    assert [s.id for s in stars] == [star.id]
    assert [d.id for d in directors] == [director.id]


@pytest.mark.asyncio
async def test_get_genre_by_id_found_and_missing(repo, db_session):
    genre = Genre(name="Drama")
    db_session.add(genre)
    await db_session.flush()

    assert (await repo.get_genre_by_id(genre.id)).name == "Drama"
    assert await repo.get_genre_by_id(999999) is None


@pytest.mark.asyncio
async def test_list_genres_with_movie_count(repo, db_session, movie_id):
    genre = Genre(name="Adventure")
    db_session.add(genre)
    await db_session.flush()

    movie = await repo.get_by_id_with_relations(movie_id)
    movie.genres = [genre]
    await db_session.flush()

    rows = await repo.list_genres_with_movie_count()
    counts = {g.name: c for g, c in rows}
    assert counts["Adventure"] == 1


@pytest.mark.asyncio
async def test_movies_by_genre_query(repo, db_session, movie_id):
    genre = Genre(name="Mystery")
    db_session.add(genre)
    await db_session.flush()

    movie = await repo.get_by_id_with_relations(movie_id)
    movie.genres = [genre]
    await db_session.flush()

    stmt = repo.movies_by_genre_query(genre.id)
    result = await db_session.execute(stmt)
    movies = result.scalars().all()
    assert [m.id for m in movies] == [movie_id]


@pytest.mark.asyncio
async def test_favorite_add_get_remove(repo, db_session, movie_id, user_id):
    assert await repo.get_favorite(movie_id, user_id) is None

    await repo.add_favorite(movie_id, user_id)
    favorite = await repo.get_favorite(movie_id, user_id)
    assert favorite is not None

    await repo.remove_favorite(favorite)
    assert await repo.get_favorite(movie_id, user_id) is None


@pytest.mark.asyncio
async def test_favorites_base_query(repo, db_session, movie_id, user_id):
    await repo.add_favorite(movie_id, user_id)

    stmt = repo.favorites_base_query(user_id)
    result = await db_session.execute(stmt)
    movies = result.scalars().all()
    assert [m.id for m in movies] == [movie_id]


@pytest.mark.asyncio
async def test_movie_like_upsert_and_count(
        repo, db_session, movie_id, user_id
):
    assert await repo.get_movie_like(movie_id, user_id) is None

    await repo.upsert_movie_like(movie_id, user_id, LikeStatus.LIKE)
    like = await repo.get_movie_like(movie_id, user_id)
    assert like.status == LikeStatus.LIKE

    await repo.upsert_movie_like(movie_id, user_id, LikeStatus.DISLIKE)
    like = await repo.get_movie_like(movie_id, user_id)
    assert like.status == LikeStatus.DISLIKE

    assert await repo.count_likes(movie_id, LikeStatus.DISLIKE) == 1
    assert await repo.count_likes(movie_id, LikeStatus.LIKE) == 0


@pytest.mark.asyncio
async def test_rating_upsert_and_average(repo, db_session, movie_id, user_id):
    assert await repo.get_rating(movie_id, user_id) is None
    assert await repo.average_rating(movie_id) is None

    await repo.upsert_rating(movie_id, user_id, 8)
    assert (await repo.get_rating(movie_id, user_id)).rating == 8
    assert await repo.average_rating(movie_id) == 8.0

    await repo.upsert_rating(movie_id, user_id, 4)
    assert (await repo.get_rating(movie_id, user_id)).rating == 4


@pytest.mark.asyncio
async def test_comment_create_and_root_comments(
        repo, db_session, movie_id, user_id
):
    comment = Comment(movie_id=movie_id, user_id=user_id, text="Nice movie")
    await repo.create_comment(comment)
    await repo.commit()

    roots = await repo.get_root_comments(movie_id)
    assert len(roots) == 1
    assert roots[0].text == "Nice movie"

    fetched = await repo.get_comment(comment.id)
    assert fetched.id == comment.id
    assert await repo.get_comment(999999) is None


@pytest.mark.asyncio
async def test_comment_like_add_and_get(repo, db_session, movie_id, user_id):
    comment = Comment(movie_id=movie_id, user_id=user_id, text="hi")
    db_session.add(comment)
    await db_session.flush()

    assert await repo.get_comment_like(comment.id, user_id) is None

    repo.add_comment_like(comment.id, user_id)
    await repo.commit()

    like = await repo.get_comment_like(comment.id, user_id)
    assert like is not None
