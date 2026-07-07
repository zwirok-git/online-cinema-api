from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from api.dependencies import (
    get_current_admin,
    get_current_user,
    get_movie_service,
)
from models.movies import Certification, Director, Genre, Star
from schemas.movies import (
    CertificationSchema,
    CommentCreateSchema,
    CommentSchema,
    DirectorSchema,
    GenreSchema,
    GenreWithCountSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieFilterParams,
    MovieLikeCreateSchema,
    MovieListItemSchema,
    MovieRatingCreateSchema,
    MovieSearchParams,
    MovieSortField,
    MovieUpdateSchema,
    PaginatedResponseSchema,
    SortOrder,
    StarSchema,
)
from services.movies import MovieService


movies_router = APIRouter(prefix="/movies", tags=["Movies"])


@movies_router.get(
    "", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def browse_movies(
    service: Annotated[MovieService, Depends(get_movie_service)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.browse(page, per_page)


@movies_router.get(
    "/filter", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def filter_movies(
    service: Annotated[MovieService, Depends(get_movie_service)],
    filters: MovieFilterParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.filter_movies(filters, page, per_page)


@movies_router.get(
    "/sort", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def sort_movies(
    service: Annotated[MovieService, Depends(get_movie_service)],
    sort_by: MovieSortField = Query(MovieSortField.POPULARITY),
    order: SortOrder = Query(SortOrder.DESC),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.sort_movies(sort_by, order, page, per_page)


@movies_router.get(
    "/search", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def search_movies(
    service: Annotated[MovieService, Depends(get_movie_service)],
    params: MovieSearchParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.search_movies(params.query, page, per_page)


@movies_router.get("/{movie_id}", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.get_detail(movie_id)


@movies_router.post("/{movie_id}/like", status_code=status.HTTP_200_OK)
async def like_movie(
    movie_id: int,
    payload: MovieLikeCreateSchema,
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    await service.like_movie(movie_id, user_id, payload.status)
    return {"detail": "Saved."}


@movies_router.post("/{movie_id}/rate", status_code=status.HTTP_200_OK)
async def rate_movie(
    movie_id: int,
    payload: MovieRatingCreateSchema,
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    await service.rate_movie(movie_id, user_id, payload.rating)
    return {"detail": "Rate saved."}


@movies_router.get("/{movie_id}/comments", response_model=list[CommentSchema])
async def get_comments(
    movie_id: int,
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.get_movie_comments(movie_id)


@movies_router.post(
    "/{movie_id}/comments",
    response_model=CommentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    movie_id: int,
    payload: CommentCreateSchema,
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.create_comment(movie_id, user_id, payload)


@movies_router.post(
    "/admin",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    payload: MovieCreateSchema,
    admin: Annotated[int, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.create_movie(payload)


@movies_router.patch("/admin/{movie_id}", response_model=MovieDetailSchema)
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    admin: Annotated[int, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.update_movie(movie_id, payload)


@movies_router.delete(
    "/admin/{movie_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
    movie_id: int,
    admin: Annotated[int, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    await service.delete_movie(movie_id)


favorites_router = APIRouter(prefix="/favorites", tags=["Favorites"])


@favorites_router.post("/{movie_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    movie_id: int,
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    await service.add_to_favorites(movie_id, user_id)
    return {"detail": "Added to favorites."}


@favorites_router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    movie_id: int,
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    await service.remove_from_favorites(movie_id, user_id)


@favorites_router.get(
    "", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def browse_favorites(
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.browse_favorites(user_id, page, per_page)


@favorites_router.get(
    "/filter", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def filter_favorites(
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
    filters: MovieFilterParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.filter_favorites(user_id, filters, page, per_page)


@favorites_router.get(
    "/sort", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def sort_favorites(
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
    sort_by: MovieSortField = Query(MovieSortField.POPULARITY),
    order: SortOrder = Query(SortOrder.DESC),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.sort_favorites(
        user_id, sort_by, order, page, per_page
    )


@favorites_router.get(
    "/search", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def search_favorites(
    user_id: Annotated[int, Depends(get_current_user)],
    service: Annotated[MovieService, Depends(get_movie_service)],
    params: MovieSearchParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.search_favorites(
        user_id, params.query, page, per_page
    )


genres_router = APIRouter(prefix="/genres", tags=["Genres"])


@genres_router.get("", response_model=list[GenreWithCountSchema])
async def list_genres(
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.list_genres_with_count()


@genres_router.get(
    "/{genre_id}/movies",
    response_model=PaginatedResponseSchema[MovieListItemSchema],
)
async def get_movies_by_genre(
    genre_id: int,
    service: Annotated[MovieService, Depends(get_movie_service)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await service.get_movies_by_genre(genre_id, page, per_page)


@genres_router.post(
    "/admin", response_model=GenreSchema, status_code=status.HTTP_201_CREATED
)
async def create_genre(
    name: str,
    admin: Annotated[int, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.create_dictionary_item(Genre, name)


@genres_router.patch("/admin/{item_id}", response_model=GenreSchema)
async def update_genre(
    item_id: int,
    name: str,
    admin: Annotated[int, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.update_dictionary_item(Genre, item_id, name)


@genres_router.delete(
    "/admin/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_genre(
    item_id: int,
    admin: Annotated[int, Depends(get_current_admin)],
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    await service.delete_dictionary_item(Genre, item_id)


stars_router = APIRouter(
    prefix="/stars", tags=["Stars"], dependencies=[Depends(get_current_admin)]
)


@stars_router.post(
    "", response_model=StarSchema, status_code=status.HTTP_201_CREATED
)
async def create_star(
    name: str, service: Annotated[MovieService, Depends(get_movie_service)]
):
    return await service.create_dictionary_item(Star, name)


@stars_router.patch("/{item_id}", response_model=StarSchema)
async def update_star(
    item_id: int,
    name: str,
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.update_dictionary_item(Star, item_id, name)


@stars_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_star(
    item_id: int, service: Annotated[MovieService, Depends(get_movie_service)]
):
    await service.delete_dictionary_item(Star, item_id)


directors_router = APIRouter(
    prefix="/directors",
    tags=["Directors"],
    dependencies=[Depends(get_current_admin)],
)


@directors_router.post(
    "", response_model=DirectorSchema, status_code=status.HTTP_201_CREATED
)
async def create_director(
    name: str, service: Annotated[MovieService, Depends(get_movie_service)]
):
    return await service.create_dictionary_item(Director, name)


@directors_router.patch("/{item_id}", response_model=DirectorSchema)
async def update_director(
    item_id: int,
    name: str,
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.update_dictionary_item(Director, item_id, name)


@directors_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_director(
    item_id: int, service: Annotated[MovieService, Depends(get_movie_service)]
):
    await service.delete_dictionary_item(Director, item_id)


certifications_router = APIRouter(
    prefix="/certifications",
    tags=["Certifications"],
    dependencies=[Depends(get_current_admin)],
)


@certifications_router.post(
    "", response_model=CertificationSchema, status_code=status.HTTP_201_CREATED
)
async def create_certification(
    name: str, service: Annotated[MovieService, Depends(get_movie_service)]
):
    return await service.create_dictionary_item(Certification, name)


@certifications_router.patch("/{item_id}", response_model=CertificationSchema)
async def update_certification(
    item_id: int,
    name: str,
    service: Annotated[MovieService, Depends(get_movie_service)],
):
    return await service.update_dictionary_item(Certification, item_id, name)


@certifications_router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_certification(
    item_id: int, service: Annotated[MovieService, Depends(get_movie_service)]
):
    await service.delete_dictionary_item(Certification, item_id)
