from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_current_admin, get_movie_service
from models.users import UserModel
from schemas.admin_movies import (
    AdminMovieCreateSchema,
    AdminMovieResponseSchema,
    AdminMovieUpdateSchema,
)
from services.movies import (
    MovieNotFoundError,
    MoviePurchasedError,
    MovieService,
    RelatedMovieDataError,
)


router = APIRouter(prefix="/admin/movies", tags=["Admin Movies"])


@router.get("", response_model=list[AdminMovieResponseSchema])
async def list_movies(
    current_admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
    limit: Annotated[int, Query(gt=0, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    movies, _total = await service.list_movies(limit=limit, offset=offset)
    return movies


@router.post(
    "",
    response_model=AdminMovieResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    payload: AdminMovieCreateSchema,
    current_admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    try:
        return await service.create_movie(payload)
    except RelatedMovieDataError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from None


@router.get("/{movie_id}", response_model=AdminMovieResponseSchema)
async def get_movie(
    movie_id: int,
    current_admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    try:
        return await service.get_movie(movie_id)
    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from None


@router.patch("/{movie_id}", response_model=AdminMovieResponseSchema)
async def update_movie(
    movie_id: int,
    payload: AdminMovieUpdateSchema,
    current_admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    try:
        return await service.update_movie(movie_id, payload)
    except MovieNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except RelatedMovieDataError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    current_admin: Annotated[UserModel, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    try:
        await service.delete_movie(movie_id)
    except MovieNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except MoviePurchasedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
