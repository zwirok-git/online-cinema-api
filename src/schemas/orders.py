from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from models.orders import OrderStatus


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    price_at_order: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    total_amount: Decimal | None
    created_at: datetime
    items: list[OrderItemResponse]


class c(OrderResponse):
    """Returned when placing an order; has warnings about
    movies that were excluded (unavailable / already purchased)."""

    excluded_movies: list[str] = []
