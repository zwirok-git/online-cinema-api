from decimal import Decimal

import pytest

from exceptions.carts import (
    CartItemNotFoundError,
    MovieAlreadyInCartError,
    MovieAlreadyPurchasedError,
)
from models.carts import Cart, CartItem
from models.movies import Movie
from services.carts import CartService


class FakeCartRepository:
    """Stands in for the real repository. No database, no session -
    just canned answers we control per test."""

    def __init__(self, cart=None, item=None, movie=None, carts_with_movie=None):
        self.cart = cart or Cart(id=1, user_id=1, items=[])
        self.item = item
        self.movie = movie
        self.carts_with_movie = carts_with_movie or []

    async def get_or_create_cart(self, user_id):
        return self.cart

    async def get_item(self, cart_id, movie_id):
        return self.item

    async def add_item(self, cart_id, movie_id):
        return CartItem(
            id=1, cart_id=cart_id, movie_id=movie_id, movie=self.movie
        )

    async def remove_item(self, cart_id, movie_id):
        return self.item is not None

    async def clear_cart(self, cart_id):
        return None

    async def get_all_carts(self, limit, offset):
        return [self.cart]

    async def get_carts_containing_movie(self, movie_id):
        return self.carts_with_movie


class FakeOrderRepository:
    def __init__(self, purchased=None):
        self.purchased = purchased or set()

    async def get_purchased_movie_ids(self, user_id):
        return self.purchased


class FakeUserRepository:
    def __init__(self, moderator_emails=None):
        self.moderator_emails = moderator_emails or []

    async def get_moderator_emails(self):
        return self.moderator_emails


def _make_service(cart_repo=None, order_repo=None, user_repo=None):
    return CartService(
        cart_repo=cart_repo or FakeCartRepository(),
        order_repo=order_repo or FakeOrderRepository(),
        user_repo=user_repo or FakeUserRepository(),
    )


async def test_add_to_cart_adds_item():
    movie = Movie(id=1, name="Avatar", price=Decimal("13.25"), year=2009)
    service = _make_service(cart_repo=FakeCartRepository(movie=movie))

    result = await service.add_to_cart(user_id=1, movie_id=1)

    assert result.movie_id == 1
    assert result.name == "Avatar"


async def test_add_to_cart_rejects_already_purchased():
    service = _make_service(order_repo=FakeOrderRepository(purchased={1}))

    with pytest.raises(MovieAlreadyPurchasedError):
        await service.add_to_cart(user_id=1, movie_id=1)


async def test_add_to_cart_rejects_duplicate():
    existing = CartItem(id=1, cart_id=1, movie_id=1)
    service = _make_service(cart_repo=FakeCartRepository(item=existing))

    with pytest.raises(MovieAlreadyInCartError):
        await service.add_to_cart(user_id=1, movie_id=1)


async def test_remove_missing_item_raises():
    service = _make_service(cart_repo=FakeCartRepository(item=None))

    with pytest.raises(CartItemNotFoundError):
        await service.remove_from_cart(user_id=1, movie_id=1)


async def test_remove_existing_item_succeeds():
    existing = CartItem(id=1, cart_id=1, movie_id=1)
    service = _make_service(cart_repo=FakeCartRepository(item=existing))

    await service.remove_from_cart(user_id=1, movie_id=1)


async def test_notify_skipped_when_movie_not_in_any_cart(monkeypatch):
    sent = []
    monkeypatch.setattr(
        "services.carts.send_email",
        lambda to, subject, html_body: sent.append(to),
    )
    service = _make_service(
        cart_repo=FakeCartRepository(carts_with_movie=[]),
        user_repo=FakeUserRepository(moderator_emails=["mod@x.com"]),
    )

    await service.notify_moderators_before_delete(
        movie_id=1, movie_title="Avatar", reason="test"
    )

    assert sent == []


async def test_notify_sends_email_to_all_moderators(monkeypatch):
    sent = []

    async def fake_send_email(to, subject, html_body):
        sent.append(to)

    monkeypatch.setattr("services.carts.send_email", fake_send_email)

    cart = Cart(id=1, user_id=2)
    service = _make_service(
        cart_repo=FakeCartRepository(carts_with_movie=[cart]),
        user_repo=FakeUserRepository(
            moderator_emails=["mod1@x.com", "mod2@x.com"]
        ),
    )

    await service.notify_moderators_before_delete(
        movie_id=1, movie_title="Avatar", reason="Deletion requested"
    )

    assert sent == ["mod1@x.com", "mod2@x.com"]
