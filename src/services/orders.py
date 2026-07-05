from exceptions.orders import (
    EmptyCartError,
    OrderNotCancelableError,
    OrderNotFoundError,
)
from models.movies import Movie
from models.orders import Order, OrderStatus
from repositories.orders import OrderRepository
from schemas.orders import OrderCreateResponse


class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def create_order(
        self, user_id: int, cart_movie_ids: list[int]
    ) -> OrderCreateResponse:
        # TODO: fetch ids via CartRepository once the carts PR merges;
        #  for now the caller passes the user's cart contents.
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
                excluded.append(f"'{movie.name}' already purchased.")
            elif movie.id in pending:
                excluded.append(
                    f"'{movie.name}' already in another pending order."
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
