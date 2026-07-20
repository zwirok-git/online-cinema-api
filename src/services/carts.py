import contextlib

from exceptions.carts import (
    CartItemNotFoundError,
    MovieAlreadyInCartError,
    MovieAlreadyPurchasedError,
)
from exceptions.notifications import EmailDeliveryException
from models.carts import Cart, CartItem
from models.notifications import NotificationType
from repositories.carts import CartRepository
from repositories.orders import OrderRepository
from repositories.users import UserRepository
from schemas.carts import CartItemResponse, CartResponse
from services.email import send_email
from services.notification_templates import get_subject, render_template


class CartService:
    def __init__(
        self,
        cart_repo: CartRepository,
        order_repo: OrderRepository,
        user_repo: UserRepository,
    ):
        self.cart_repo = cart_repo
        self.order_repo = order_repo
        self.user_repo = user_repo

    async def add_to_cart(
        self, user_id: int, movie_id: int
    ) -> CartItemResponse:
        purchased = await self.order_repo.get_purchased_movie_ids(user_id)
        if movie_id in purchased:
            raise MovieAlreadyPurchasedError(
                "This movie has already been purchased."
            )

        cart = await self.cart_repo.get_or_create_cart(user_id)

        existing_item = await self.cart_repo.get_item(cart.id, movie_id)
        if existing_item is not None:
            raise MovieAlreadyInCartError(
                "This movie is already in your cart."
            )

        item = await self.cart_repo.add_item(cart.id, movie_id)
        return self._to_item_response(item)

    async def remove_from_cart(self, user_id: int, movie_id: int) -> None:
        cart = await self.cart_repo.get_or_create_cart(user_id)
        removed = await self.cart_repo.remove_item(cart.id, movie_id)
        if not removed:
            raise CartItemNotFoundError("This movie is not in your cart.")

    async def clear_cart(self, user_id: int) -> None:
        cart = await self.cart_repo.get_or_create_cart(user_id)
        await self.cart_repo.clear_cart(cart.id)

    async def get_cart_contents(self, user_id: int) -> CartResponse:
        cart = await self.cart_repo.get_or_create_cart(user_id)
        return self._to_cart_response(cart)

    async def get_all_carts(
        self, limit: int, offset: int
    ) -> list[CartResponse]:
        carts = await self.cart_repo.get_all_carts(limit, offset)
        return [self._to_cart_response(cart) for cart in carts]

    async def notify_moderators_before_delete(
        self, movie_id: int, movie_title: str, reason: str
    ) -> None:
        carts = await self.cart_repo.get_carts_containing_movie(movie_id)
        if not carts:
            return

        moderator_emails = await self.user_repo.get_moderator_emails()
        context = {
            "movie_title": movie_title,
            "reason": reason,
            "affected_users_count": len(carts),
        }
        subject = get_subject(NotificationType.MODERATOR_MOVIE_DELETE_WARNING)
        html_body = render_template(
            NotificationType.MODERATOR_MOVIE_DELETE_WARNING, context
        )
        for email in moderator_emails:
            with contextlib.suppress(EmailDeliveryException):
                send_email(to=email, subject=subject, html_body=html_body)

    @staticmethod
    def _to_item_response(item: CartItem) -> CartItemResponse:
        return CartItemResponse(
            id=item.id,
            movie_id=item.movie_id,
            name=item.movie.name,
            price=item.movie.price,
            year=item.movie.year,
            genres=[genre.name for genre in item.movie.genres],
        )

    @classmethod
    def _to_cart_response(cls, cart: Cart) -> CartResponse:
        return CartResponse(
            id=cart.id,
            items=[cls._to_item_response(item) for item in cart.items],
        )
