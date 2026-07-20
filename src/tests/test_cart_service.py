from decimal import Decimal

import pytest
from sqlalchemy import select

from exceptions.carts import (
    CartItemNotFoundError,
    MovieAlreadyInCartError,
    MovieAlreadyPurchasedError,
)
from models.movies import Certification, Movie
from models.orders import OrderStatus
from models.users import UserGroupEnum, UserGroupModel, UserModel
from repositories.carts import CartRepository
from repositories.orders import OrderRepository
from repositories.users import UserRepository
from services.carts import CartService


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


async def _make_user(
    db_session, email: str, group: UserGroupEnum = UserGroupEnum.USER
) -> UserModel:
    result = await db_session.execute(
        select(UserGroupModel).where(UserGroupModel.name == group)
    )
    group_row = result.scalar_one()
    user = UserModel(
        email=email,
        hashed_password="x",
        group_id=group_row.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def _service(db_session) -> CartService:
    return CartService(
        cart_repo=CartRepository(db_session),
        order_repo=OrderRepository(db_session),
        user_repo=UserRepository(db_session),
    )


async def test_add_to_cart_adds_item(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")

    result = await _service(db_session).add_to_cart(
        user_id=test_user.id, movie_id=avatar.id
    )

    assert result.movie_id == avatar.id
    assert result.name == "Avatar"


async def test_add_to_cart_rejects_already_purchased(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    order_repo = OrderRepository(db_session)
    order = await order_repo.create_order(test_user.id, [avatar])
    await order_repo.update_status(order, OrderStatus.PAID)

    with pytest.raises(MovieAlreadyPurchasedError):
        await _service(db_session).add_to_cart(
            user_id=test_user.id, movie_id=avatar.id
        )


async def test_add_to_cart_rejects_duplicate(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    service = _service(db_session)
    await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)

    with pytest.raises(MovieAlreadyInCartError):
        await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)


async def test_remove_missing_item_raises(db_session, test_user):
    with pytest.raises(CartItemNotFoundError):
        await _service(db_session).remove_from_cart(
            user_id=test_user.id, movie_id=999
        )


async def test_remove_existing_item_succeeds(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    service = _service(db_session)
    await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)

    await service.remove_from_cart(user_id=test_user.id, movie_id=avatar.id)

    cart = await service.get_cart_contents(test_user.id)
    assert cart.items == []


async def test_get_cart_contents_returns_items(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    titanic = await _make_movie(db_session, 2, "Titanic", "14.20")
    service = _service(db_session)
    await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)
    await service.add_to_cart(user_id=test_user.id, movie_id=titanic.id)

    cart = await service.get_cart_contents(test_user.id)

    assert {item.movie_id for item in cart.items} == {avatar.id, titanic.id}


async def test_clear_cart_removes_all_items(db_session, test_user):
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    service = _service(db_session)
    await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)

    await service.clear_cart(test_user.id)

    cart = await service.get_cart_contents(test_user.id)
    assert cart.items == []


async def test_get_all_carts_includes_every_user(db_session, test_user):
    stranger = await _make_user(db_session, "stranger@example.com")
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    service = _service(db_session)
    await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)
    await service.add_to_cart(user_id=stranger.id, movie_id=avatar.id)

    carts = await service.get_all_carts(limit=20, offset=0)

    assert len(carts) == 2
    for cart in carts:
        assert [item.movie_id for item in cart.items] == [avatar.id]


async def test_notify_skipped_when_movie_not_in_any_cart(db_session, test_user, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "services.carts.send_email",
        lambda to, subject, html_body: sent.append(to),
    )
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")

    await _service(db_session).notify_moderators_before_delete(
        movie_id=avatar.id, movie_title="Avatar", reason="test"
    )

    assert sent == []


async def test_notify_sends_email_to_all_moderators(db_session, test_user, monkeypatch):
    sent = []

    def fake_send_email(to, subject, html_body):
        sent.append(to)

    monkeypatch.setattr("services.carts.send_email", fake_send_email)

    moderator = await _make_user(
        db_session, "mod1@example.com", group=UserGroupEnum.MODERATOR
    )
    admin = await _make_user(
        db_session, "mod2@example.com", group=UserGroupEnum.ADMIN
    )
    avatar = await _make_movie(db_session, 1, "Avatar", "13.25")
    service = _service(db_session)
    await service.add_to_cart(user_id=test_user.id, movie_id=avatar.id)

    await service.notify_moderators_before_delete(
        movie_id=avatar.id, movie_title="Avatar", reason="Deletion requested"
    )

    assert set(sent) == {moderator.email, admin.email}
