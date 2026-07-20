from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import (
    get_cart_service,
    get_current_admin,
    get_current_user,
)
from exceptions.carts import (
    CartItemNotFoundError,
    MovieAlreadyInCartError,
    MovieAlreadyPurchasedError,
)
from models.users import UserModel
from schemas.carts import (
    CartItemCreateRequest,
    CartItemResponse,
    CartResponse,
)
from services.carts import CartService


router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a movie to the cart",
)
async def add_to_cart(
    payload: CartItemCreateRequest,
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[CartService, Depends(get_cart_service)],
):
    """Adding an already-purchased movie is rejected with a 403;
    adding a movie already in the cart is rejected with a 409."""
    try:
        return await service.add_to_cart(user.id, payload.movie_id)
    except MovieAlreadyPurchasedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        ) from None
    except MovieAlreadyInCartError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        ) from None


@router.delete(
    "/items/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a movie from the cart",
)
async def remove_from_cart(
    movie_id: int,
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[CartService, Depends(get_cart_service)],
):
    try:
        await service.remove_from_cart(user.id, movie_id)
    except CartItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from None


@router.get(
    "",
    response_model=CartResponse,
    summary="View my cart",
)
async def get_cart(
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[CartService, Depends(get_cart_service)],
):
    """For each movie: title, price, genres, and release year."""
    return await service.get_cart_contents(user.id)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear the cart",
)
async def clear_cart(
    user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[CartService, Depends(get_cart_service)],
):
    await service.clear_cart(user.id)


@router.get(
    "/admin/all",
    response_model=list[CartResponse],
    summary="List all carts (moderator/admin only)",
)
async def get_all_carts(
    admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[CartService, Depends(get_cart_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Moderator/admin view of every user's cart, for
    troubleshooting and analysis."""
    return await service.get_all_carts(limit=limit, offset=offset)
