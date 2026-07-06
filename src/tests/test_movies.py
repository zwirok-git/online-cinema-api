from decimal import Decimal

import pytest

from exceptions.movies import (
    FavoriteNotFoundError,
    MovieAlreadyExistsError,
    MovieHasPurchasesError,
    MovieNotFoundError,
    DictionaryItemAlreadyExistsError,
    GenreNotFoundError
)

from models.movies import Certification, Genre, Movie
from models.users import UserGroupEnum, UserGroupModel, UserModel
from repositories.movies import MovieRepository
from schemas.movies import MovieCreateSchema
from services.movies import MovieService


@pytest.fixture
async def user_group_id(db_session):
    group = UserGroupModel(name=UserGroupEnum.USER)
    db_session.add(group)
    await db_session.flush()
    return group.id


@pytest.fixture
async def user_id(db_session, user_group_id):
    user = UserModel(email="svc@test.com", hashed_password="x", is_active=True, group_id=user_group_id)
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def second_user_id(db_session, user_group_id):
    user = UserModel(email="svc2@test.com", hashed_password="x", is_active=True, group_id=user_group_id)
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def certification_id(db_session):
    cert = Certification(name="R")
    db_session.add(cert)
    await db_session.flush()
    return cert.id


@pytest.fixture
def service(db_session):
    return MovieService(MovieRepository(db_session))


@pytest.mark.asyncio
async def test_dictionary_item_duplicate_raises(service):
    await service.create_dictionary_item(Genre, "Unique Genre")
    with pytest.raises(DictionaryItemAlreadyExistsError):
        await service.create_dictionary_item(Genre, "Unique Genre")


@pytest.mark.asyncio
async def test_add_to_favorites_raises_when_movie_missing(service):
    with pytest.raises(Exception):
        await service.add_to_favorites(999999, user_id=1)


@pytest.mark.asyncio
async def test_update_and_delete_dictionary_item_not_found(service):
    with pytest.raises(GenreNotFoundError):
        await service.update_dictionary_item(Genre, 999999, "X")

    with pytest.raises(GenreNotFoundError):
        await service.delete_dictionary_item(Genre, 999999)


@pytest.mark.asyncio
async def test_update_dictionary_item_duplicate_raises(service):
    await service.create_dictionary_item(Genre, "Name A")
    item_b = await service.create_dictionary_item(Genre, "Name B")

    with pytest.raises(DictionaryItemAlreadyExistsError):
        await service.update_dictionary_item(Genre, item_b.id, "Name A")


@pytest.mark.asyncio
async def test_update_and_delete_dictionary_item_success(service):
    item = await service.create_dictionary_item(Genre, "Temp Genre")

    updated = await service.update_dictionary_item(Genre, item.id, "Renamed Genre")
    assert updated.name == "Renamed Genre"

    await service.delete_dictionary_item(Genre, item.id)


class FakeMovieRepository:
    def __init__(self, movie=None, has_purchases=False, create_ok=True, favorite=None):
        self.movie = movie
        self._has_purchases = has_purchases
        self._create_ok = create_ok
        self.favorite = favorite
        self.deleted = False
        self.favorited = False

    async def get_by_id(self, movie_id):
        return self.movie

    async def get_by_id_with_relations(self, movie_id):
        return self.movie

    async def has_purchases(self, movie_id):
        return self._has_purchases

    async def delete_movie(self, movie):
        self.deleted = True

    async def create_movie(self, movie):
        return self._create_ok

    async def get_genres_by_ids(self, ids):
        return []

    async def get_stars_by_ids(self, ids):
        return []

    async def get_directors_by_ids(self, ids):
        return []

    async def get_favorite(self, movie_id, user_id):
        return self.favorite

    async def add_favorite(self, movie_id, user_id):
        self.favorited = True

    async def remove_favorite(self, favorite):
        self.favorited = False

    async def upsert_movie_like(self, movie_id, user_id, status_):
        pass


@pytest.mark.asyncio
async def test_get_detail_raises_when_movie_missing():
    service = MovieService(repo=FakeMovieRepository(movie=None))

    with pytest.raises(MovieNotFoundError):
        await service.get_detail(movie_id=1)


@pytest.mark.asyncio
async def test_create_movie_raises_on_duplicate():
    service = MovieService(repo=FakeMovieRepository(create_ok=False))
    payload = MovieCreateSchema(
        name="Dune", year=2021, time=155, imdb=8.0, votes=100,
        description="d", certification_id=1,
    )

    with pytest.raises(MovieAlreadyExistsError):
        await service.create_movie(payload)


@pytest.mark.asyncio
async def test_delete_movie_raises_when_missing():
    service = MovieService(repo=FakeMovieRepository(movie=None))

    with pytest.raises(MovieNotFoundError):
        await service.delete_movie(movie_id=1)


@pytest.mark.asyncio
async def test_delete_movie_raises_when_purchased():
    movie = Movie(id=1, name="Dune", price=Decimal("9.99"))
    service = MovieService(repo=FakeMovieRepository(movie=movie, has_purchases=True))

    with pytest.raises(MovieHasPurchasesError):
        await service.delete_movie(movie_id=1)


@pytest.mark.asyncio
async def test_delete_movie_success():
    movie = Movie(id=1, name="Dune", price=Decimal("9.99"))
    repo = FakeMovieRepository(movie=movie, has_purchases=False)
    service = MovieService(repo=repo)

    await service.delete_movie(movie_id=1)

    assert repo.deleted is True


@pytest.mark.asyncio
async def test_remove_from_favorites_raises_when_not_favorited():
    service = MovieService(repo=FakeMovieRepository(favorite=None))

    with pytest.raises(FavoriteNotFoundError):
        await service.remove_from_favorites(movie_id=1, user_id=1)


@pytest.mark.asyncio
async def test_like_movie_raises_when_movie_missing():
    service = MovieService(repo=FakeMovieRepository(movie=None))

    with pytest.raises(MovieNotFoundError):
        await service.like_movie(movie_id=1, user_id=1, status_="like")
