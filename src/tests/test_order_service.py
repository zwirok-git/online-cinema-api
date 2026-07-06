from datetime import datetime, timezone
from decimal import Decimal

import pytest

from exceptions.orders import EmptyCartError, OrderNotFoundError
from models.movies import Movie
from models.orders import Order, OrderItem, OrderStatus
from services.orders import OrderService


class FakeOrderRepository:
    """Stands in for the real repository. No database, no session -
    just canned answers we control per test."""

    def __init__(
        self, cart_ids=None, movies=None, purchased=None, pending=None, order=None
    ):
        self.cart_ids = cart_ids or []
        self.movies = movies or []
        self.purchased = purchased or set()
        self.pending = pending or set()
        self.order = order

    async def get_cart_movie_ids(self, user_id):
        return self.cart_ids

    async def get_movies_by_ids(self, movie_ids):
        return [m for m in self.movies if m.id in movie_ids]

    async def get_purchased_movie_ids(self, user_id):
        return self.purchased

    async def get_pending_movie_ids(self, user_id):
        return self.pending

    async def create_order(self, user_id, movies):
        return Order(
            id=1,
            user_id=user_id,
            status=OrderStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            total_amount=sum(
                (movie.price for movie in movies), Decimal("0.00")
            ),
            items=[
                OrderItem(
                    id=index,
                    movie_id=movie.id,
                    price_at_order=movie.price,
                )
                for index, movie in enumerate(movies, start=1)
            ],
        )

    async def get_order_by_id(self, order_id):
        return self.order

    async def update_status(self, order, status):
        order.status = status
        return order


async def test_create_order_with_empty_cart_is_refused():
    service = OrderService(repo=FakeOrderRepository(cart_ids=[]))

    with pytest.raises(EmptyCartError):
        await service.create_order(user_id=1)


async def test_purchased_movie_is_excluded_from_order():
    avatar = Movie(id=1, name="Avatar", price=Decimal("13.25"))
    titanic = Movie(id=2, name="Titanic", price=Decimal("14.20"))
    repo = FakeOrderRepository(
        cart_ids=[1, 2],
        movies=[avatar, titanic],
        purchased={1},
    )
    service = OrderService(repo=repo)

    response = await service.create_order(user_id=1)

    assert len(response.items) == 1
    assert response.items[0].movie_id == 2
    assert len(response.excluded_movies) == 1
    assert "Avatar" in response.excluded_movies[0]


async def test_pending_movie_is_excluded_from_order():
    avatar = Movie(id=1, name="Avatar", price=Decimal("13.25"))
    titanic = Movie(id=2, name="Titanic", price=Decimal("14.20"))
    repo = FakeOrderRepository(
        cart_ids=[1, 2],
        movies=[avatar, titanic],
        pending={1},
    )
    service = OrderService(repo=repo)

    response = await service.create_order(user_id=1)

    assert len(response.items) == 1
    assert response.items[0].movie_id == 2
    assert len(response.excluded_movies) == 1
    assert "pending" in response.excluded_movies[0]


async def test_unavailable_movie_is_excluded_from_order():
    avatar = Movie(id=1, name="Avatar", price=Decimal("13.25"))
    titanic = Movie(id=2, name="Titanic", price=Decimal("14.20"))
    repo = FakeOrderRepository(
        cart_ids=[1, 2, 3],
        movies=[avatar, titanic],
    )
    service = OrderService(repo=repo)

    response = await service.create_order(user_id=1)

    assert len(response.items) == 2
    assert response.items[0].movie_id == 1
    assert len(response.excluded_movies) == 1
    assert "no longer available" in response.excluded_movies[0]


async def test_order_with_nothing_payable_is_refused():
    avatar = Movie(id=1, name="Avatar", price=Decimal("13.25"))
    repo = FakeOrderRepository(
        cart_ids=[1],
        movies=[avatar],
        purchased={1}
    )
    service = OrderService(repo=repo)

    with pytest.raises(EmptyCartError):
        await service.create_order(user_id=1)


async def test_order_placement_success():
    avatar = Movie(id=1, name="Avatar", price=Decimal("13.25"))
    titanic = Movie(id=2, name="Titanic", price=Decimal("14.20"))
    repo = FakeOrderRepository(
        cart_ids=[1, 2],
        movies=[avatar, titanic],
    )
    service = OrderService(repo=repo)
    response = await service.create_order(user_id=1)

    assert len(response.items) == 2
    assert response.total_amount == Decimal("27.45")
    assert response.status == OrderStatus.PENDING
    assert response.excluded_movies == []


async def test_order_not_found():
    repo = FakeOrderRepository()
    service = OrderService(repo=repo)

    with pytest.raises(OrderNotFoundError):
        await service.get_order(user_id=1, order_id=77)


async def test_foreign_order_is_not_found():
    repo = FakeOrderRepository(
        order=Order(id=5, user_id=999, status=OrderStatus.PENDING)
    )
    service = OrderService(repo=repo)

    with pytest.raises(OrderNotFoundError):
        await service.get_order(user_id=1, order_id=5)