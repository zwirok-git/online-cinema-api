from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from models.carts import Cart, CartItem
from models.movies import Certification, Movie
from models.orders import OrderStatus
from repositories.orders import OrderRepository


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


async def test_create_order_writes_to_database(db_session, test_user):
    movie = await _make_movie(db_session, 1, "Inception", "19.99")
    repo = OrderRepository(db_session)

    order = await repo.create_order(user_id=test_user.id, movies=[movie])

    saved = await repo.get_order_by_id(order.id)
    assert saved is not None
    assert saved.total_amount == Decimal("19.99")
    assert saved.items[0].price_at_order == Decimal("19.99")


async def test_purchased_ids_come_from_paid_orders_only(db_session, test_user):
    movie = await _make_movie(db_session, 2, "Dune", "14.99")
    repo = OrderRepository(db_session)

    order = await repo.create_order(user_id=test_user.id, movies=[movie])
    assert await repo.get_purchased_movie_ids(test_user.id) == set()

    await repo.update_status(order, OrderStatus.PAID)
    assert await repo.get_purchased_movie_ids(test_user.id) == {2}


async def test_status_update_is_persisted(db_session, test_user):
    movie = await _make_movie(db_session, 3, "Tenet", "9.99")
    repo = OrderRepository(db_session)
    order = await repo.create_order(user_id=test_user.id, movies=[movie])

    await repo.update_status(order, OrderStatus.CANCELED)

    reloaded = await repo.get_order_by_id(order.id)
    assert reloaded.status == OrderStatus.CANCELED


async def test_duplicate_cart_item_rejected_by_database(db_session, test_user):
    movie = await _make_movie(db_session, 4, "Dune 2", "12.99")
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.flush()

    db_session.add(CartItem(cart_id=cart.id, movie_id=movie.id))
    await db_session.flush()

    db_session.add(CartItem(cart_id=cart.id, movie_id=movie.id))
    with pytest.raises(IntegrityError):
        await db_session.flush()
