from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_db
from exceptions.orders import (
    EmptyCartError,
    OrderNotCancelableError,
    OrderNotFoundError,
)
from models.orders import OrderStatus
from models.users import UserModel
from repositories.orders import OrderRepository
from schemas.orders import OrderCreateResponse, OrderResponse
from services.orders import OrderService


router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderService:
    return OrderService(repo=OrderRepository(db))


@router.post(
    "",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order from the cart",
)
async def create_order(
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
    cart_movie_ids: list[int],  # TODO: remove once cart integration lands
):
    """Creates an order from the user's cart. Movies that are
    unavailable or already purchased are excluded and reported
    in `excluded_movies`."""
    try:
        return await service.create_order(user.id, cart_movie_ids)
    except EmptyCartError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from None


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List my orders",
)
async def get_my_orders(
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Order history: date, movies, total and status for each order."""
    return await service.get_user_orders(user.id)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get one of my orders",
)
async def get_order(
    order_id: int,
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    try:
        return await service.get_order(user.id, order_id)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from None


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel a pending order",
)
async def cancel_order(
    order_id: int,
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Only pending orders can be canceled. Paid orders require
    a refund request."""
    try:
        return await service.cancel_order(user.id, order_id)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from None
    except OrderNotCancelableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        ) from None


@router.get(
    "/admin/all",
    response_model=list[OrderResponse],
    summary="List all orders (moderator/admin only)",
)
async def get_all_orders(
    admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[OrderService, Depends(get_order_service)],
    user_id: int | None = None,
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    """Filter by user, status, or date range."""
    return await service.get_all_orders(
        user_id=user_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )
