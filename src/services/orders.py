import contextlib
from datetime import datetime, timezone

from exceptions.notifications import EmailDeliveryException
from exceptions.orders import (
    EmptyCartError,
    OrderNotCancelableError,
    OrderNotFoundError,
    OrderNotPayableError,
)
from models.movies import Movie
from models.notifications import NotificationType
from models.orders import Order, OrderStatus
from repositories.orders import OrderRepository
from schemas.orders import OrderCreateResponse
from services.email import send_email
from services.notification_templates import get_subject, render_template


class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def create_order(self, user_id: int) -> OrderCreateResponse:
        cart_movie_ids = await self.repo.get_cart_movie_ids(user_id)
        if not cart_movie_ids:
            raise EmptyCartError("Your cart is empty.")

        movies = await self.repo.get_movies_by_ids(cart_movie_ids)
        purchased = await self.repo.get_purchased_movie_ids(user_id)
        pending = await self.repo.get_pending_movie_ids(user_id)

        excluded: list[str] = []

        found_ids = {movie.id for movie in movies}
        for movie_id in cart_movie_ids:
            if movie_id not in found_ids:
                excluded.append(f"Movie #{movie_id} is no longer available.")

        payable: list[Movie] = []
        for movie in movies:
            if movie.id in purchased:
                excluded.append(f"'{movie.name}' — already purchased.")
            elif movie.id in pending:
                excluded.append(
                    f"'{movie.name}' — already in another pending order."
                )
            else:
                payable.append(movie)

        if not payable:
            raise EmptyCartError(
                "None of the movies in your cart are available for purchase."
            )

        order = await self.repo.create_order(user_id, payable)

        response = OrderCreateResponse.model_validate(order)
        response.excluded_movies = excluded
        return response

    async def get_user_orders(self, user_id: int) -> list[Order]:
        return await self.repo.get_user_orders(user_id)

    async def get_order(self, user_id: int, order_id: int) -> Order:
        order = await self.repo.get_order_by_id(order_id)
        if order is None or order.user_id != user_id:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        return order

    async def cancel_order(self, user_id: int, order_id: int) -> Order:
        order = await self.get_order(user_id, order_id)
        if order.status == OrderStatus.PAID:
            raise OrderNotCancelableError(
                "Paid orders can only be canceled via a refund request."
            )
        if order.status == OrderStatus.CANCELED:
            raise OrderNotCancelableError("This order is already canceled.")
        return await self.repo.update_status(order, OrderStatus.CANCELED)

    async def get_all_orders(
        self,
        user_id: int | None = None,
        status: OrderStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Order]:
        return await self.repo.get_all_orders(
            user_id=user_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )

    async def mark_paid(self, order_id: int) -> Order:
        order = await self.repo.get_order_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        if order.status != OrderStatus.PENDING:
            raise OrderNotPayableError(
                f"Cannot mark {order.status} order as paid."
            )

        order = await self.repo.update_status(order, OrderStatus.PAID)

        email = await self.repo.get_user_email(order.user_id)
        if email:
            total = order.total_amount or sum(
                item.price_at_order for item in order.items
            )
            context = {
                "order_id": order.id,
                "movie_titles": [item.movie.name for item in order.items],
                "total_amount": total,
                "payment_date": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M UTC"
                ),
            }
            # payment already succeeded; email is best-effort
            with contextlib.suppress(EmailDeliveryException):
                await send_email(
                    to=email,
                    subject=get_subject(
                        NotificationType.ORDER_PAYMENT_CONFIRMATION
                    ),
                    html_body=render_template(
                        NotificationType.ORDER_PAYMENT_CONFIRMATION,
                        context,
                    ),
                )

        return order
