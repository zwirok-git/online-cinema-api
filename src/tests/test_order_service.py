import pytest

from exceptions.orders import EmptyCartError
from services.orders import OrderService


class FakeOrderRepository:
    """Stands in for the real repository. No database, no session -
    just canned answers we control per test."""

    def __init__(
        self, cart_ids=None, movies=None, purchased=None, pending=None
    ):
        self.cart_ids = cart_ids or []
        self.movies = movies or []
        self.purchased = purchased or set()
        self.pending = pending or set()

    async def get_cart_movie_ids(self, user_id):
        return self.cart_ids

    async def get_movies_by_ids(self, movie_ids):
        return [m for m in self.movies if m.id in movie_ids]

    async def get_purchased_movie_ids(self, user_id):
        return self.purchased

    async def get_pending_movie_ids(self, user_id):
        return self.pending


async def test_create_order_with_empty_cart_is_refused():
    service = OrderService(repo=FakeOrderRepository(cart_ids=[]))

    with pytest.raises(EmptyCartError):
        await service.create_order(user_id=1)