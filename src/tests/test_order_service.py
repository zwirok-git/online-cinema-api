from decimal import Decimal

import pytest
from sqlalchemy import select

from exceptions.orders import EmptyCartError, OrderNotFoundError
from models.carts import Cart, CartItem
from models.movies import Certification, Movie
from models.orders import OrderStatus
from models.users import UserGroupEnum, UserGroupModel, UserModel
from repositories.orders import OrderRepository
from services.orders import OrderService


async def _make_movie(db_session, movie_id: int, name: str, price: str) -> Movie:
    cert = await db_session.get(Certification, 1)
    if cert is None:
        cert = Certification(id=1, name="PG-13")
        db_session.add(cert)
        await db_session.flush()
    movie = Movie(
        id=movie_id,
        name=name,
        year=2020,
        time=120,
        imdb=8.0,
        votes=1000,
        description="test",
        price=Decimal(price),
        certification_id=1,
    )
    db_session.add(movie)
    await db_session.flush()
    return movie


async def _fill_cart(db_session, user_id: int, movies: list[Movie]) -> Cart:
    cart = Cart(user_id=user_id)
    db_session.add(cart)
    await db_session.flush()
    for movie in movies:
        db_session.add(CartItem(cart_id=cart.id, movie_id=movie.id))
    await db_session.flush()
    return cart


async def _make_user(db_session, email: str) -> UserModel:
    result = await db_session.execute(
        select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    )
    group = result.scalar_one()
    user = UserModel(
        email=email,
        hashed_password="x",
        group_id=group.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def _service(db_session) -> OrderService:
    return OrderService(repo=OrderRepository(db_session))


async def test_create_order_with_empty_cart_is_refused(db_session, test_user):
    with pytest.raises(EmptyCartError):
        await _service(db_session).create_order(user_id=test_user.id)


async def test_purchased_movie_is_excluded_from_order(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    titanic = await _make_movie(db_session, 2, "Titanic", "14.20")
    await _fill_cart(db_session, test_user.id, [avatar, titanic])

    repo = OrderRepository(db_session)
    old_order = await repo.create_order(test_user.id, [avatar])
    await repo.update_status(old_order, OrderStatus.PAID)

    response = await _service(db_session).create_order(user_id=test_user.id)

    assert len(response.items) == 1
    assert response.items[0].movie_id == titanic.id
    assert len(response.excluded_movies) == 1
    assert "Avatar" in response.excluded_movies[0]


async def test_pending_movie_is_excluded_from_order(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    titanic = await _make_movie(db_session, 2, "Titanic", "14.20")
    await _fill_cart(db_session, test_user.id, [avatar, titanic])

    repo = OrderRepository(db_session)
    await repo.create_order(test_user.id, [avatar])  # stays pending

    response = await _service(db_session).create_order(user_id=test_user.id)

    assert len(response.items) == 1
    assert response.items[0].movie_id == titanic.id
    assert "pending" in response.excluded_movies[0]


async def test_order_with_nothing_payable_is_refused(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    await _fill_cart(db_session, test_user.id, [avatar])

    repo = OrderRepository(db_session)
    old_order = await repo.create_order(test_user.id, [avatar])
    await repo.update_status(old_order, OrderStatus.PAID)

    with pytest.raises(EmptyCartError):
        await _service(db_session).create_order(user_id=test_user.id)


async def test_order_placement_success(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    titanic = await _make_movie(db_session, 2, "Titanic", "14.20")
    await _fill_cart(db_session, test_user.id, [avatar, titanic])

    response = await _service(db_session).create_order(user_id=test_user.id)

    assert len(response.items) == 2
    assert response.total_amount == Decimal("27.45")
    assert response.status == OrderStatus.PENDING
    assert response.excluded_movies == []


async def test_order_not_found(db_session, test_user):
    with pytest.raises(OrderNotFoundError):
        await _service(db_session).get_order(user_id=test_user.id, order_id=777)


async def test_foreign_order_is_not_found(db_session, test_user):
    stranger = await _make_user(db_session, "stranger@example.com")
    movie = await _make_movie(db_session, 1, "Avatar", "13.25")
    repo = OrderRepository(db_session)
    foreign_order = await repo.create_order(stranger.id, [movie])

    with pytest.raises(OrderNotFoundError):
        await _service(db_session).get_order(
            user_id=test_user.id, order_id=foreign_order.id
        )