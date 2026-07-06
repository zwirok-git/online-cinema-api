from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_admin, get_current_user
from core.database import get_db
from models.movies import Certification, Director, Genre, Star
from repositories.movies import MovieRepository
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


router = APIRouter()


def get_movie_service(db: AsyncSession = Depends(get_db)) -> MovieService:
    return MovieService(MovieRepository(db))


movies_router = APIRouter(prefix="/movies", tags=["Movies"])


@movies_router.get(
    "/", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def browse_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: MovieService = Depends(get_movie_service),
):
    return await service.browse(page, per_page)


@movies_router.get(
    "/filter", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def filter_movies(
    filters: MovieFilterParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: MovieService = Depends(get_movie_service),
):
    return await service.filter_movies(filters, page, per_page)


@movies_router.get(
    "/sort", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def sort_movies(
    sort_by: MovieSortField = Query(MovieSortField.POPULARITY),
    order: SortOrder = Query(SortOrder.DESC),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: MovieService = Depends(get_movie_service),
):
    return await service.sort_movies(sort_by, order, page, per_page)


@movies_router.get(
    "/search", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def search_movies(
    params: MovieSearchParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: MovieService = Depends(get_movie_service),
):
    return await service.search_movies(params.query, page, per_page)


@movies_router.get("/{movie_id}", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int, service: MovieService = Depends(get_movie_service)
):
    return await service.get_detail(movie_id)


@movies_router.post("/{movie_id}/like", status_code=status.HTTP_200_OK)
async def like_movie(
    movie_id: int,
    payload: MovieLikeCreateSchema,
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    await service.like_movie(movie_id, user_id, payload.status)
    return {"detail": "Saved."}


@movies_router.post("/{movie_id}/rate", status_code=status.HTTP_200_OK)
async def rate_movie(
    movie_id: int,
    payload: MovieRatingCreateSchema,
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    await service.rate_movie(movie_id, user_id, payload.rating)
    return {"detail": "Rate saved."}


@movies_router.get("/{movie_id}/comments", response_model=list[CommentSchema])
async def get_comments(
    movie_id: int, service: MovieService = Depends(get_movie_service)
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
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    return await service.create_comment(movie_id, user_id, payload)


favorites_router = APIRouter(prefix="/favorites", tags=["Favorites"])


@favorites_router.post("/{movie_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    movie_id: int,
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    await service.add_to_favorites(movie_id, user_id)
    return {"detail": "Added to favorites."}


@favorites_router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    movie_id: int,
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    await service.remove_from_favorites(movie_id, user_id)


@favorites_router.get(
    "/", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def browse_favorites(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    return await service.browse_favorites(user_id, page, per_page)


@favorites_router.get(
    "/filter", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def filter_favorites(
    filters: MovieFilterParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    return await service.filter_favorites(user_id, filters, page, per_page)


@favorites_router.get(
    "/sort", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def sort_favorites(
    sort_by: MovieSortField = Query(MovieSortField.POPULARITY),
    order: SortOrder = Query(SortOrder.DESC),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    return await service.sort_favorites(
        user_id, sort_by, order, page, per_page
    )


@favorites_router.get(
    "/search", response_model=PaginatedResponseSchema[MovieListItemSchema]
)
async def search_favorites(
    params: MovieSearchParams = Depends(),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
    service: MovieService = Depends(get_movie_service),
):
    return await service.search_favorites(
        user_id, params.query, page, per_page
    )


genres_router = APIRouter(prefix="/genres", tags=["Genres"])


@genres_router.get("/", response_model=list[GenreWithCountSchema])
async def list_genres(service: MovieService = Depends(get_movie_service)):
    return await service.list_genres_with_count()


@genres_router.get(
    "/{genre_id}/movies",
    response_model=PaginatedResponseSchema[MovieListItemSchema],
)
async def get_movies_by_genre(
    genre_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: MovieService = Depends(get_movie_service),
):
    return await service.get_movies_by_genre(genre_id, page, per_page)


admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin)],
)


@admin_router.post(
    "/movies",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    payload: MovieCreateSchema,
    service: MovieService = Depends(get_movie_service),
):
    return await service.create_movie(payload)


@admin_router.patch("/movies/{movie_id}", response_model=MovieDetailSchema)
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    service: MovieService = Depends(get_movie_service),
):
    return await service.update_movie(movie_id, payload)


@admin_router.delete(
    "/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
    movie_id: int,
    service: MovieService = Depends(get_movie_service),
):
    await service.delete_movie(movie_id)


@admin_router.post(
    "/genres", response_model=GenreSchema, status_code=status.HTTP_201_CREATED
)
async def create_genre(
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.create_dictionary_item(Genre, name)


@admin_router.patch("/genres/{item_id}", response_model=GenreSchema)
async def update_genre(
    item_id: int,
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.update_dictionary_item(Genre, item_id, name)


@admin_router.delete(
    "/genres/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_genre(
    item_id: int,
    service: MovieService = Depends(get_movie_service),
):
    await service.delete_dictionary_item(Genre, item_id)


@admin_router.post(
    "/stars", response_model=StarSchema, status_code=status.HTTP_201_CREATED
)
async def create_star(
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.create_dictionary_item(Star, name)


@admin_router.patch("/stars/{item_id}", response_model=StarSchema)
async def update_star(
    item_id: int,
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.update_dictionary_item(Star, item_id, name)


@admin_router.delete(
    "/stars/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_star(
    item_id: int,
    service: MovieService = Depends(get_movie_service),
):
    await service.delete_dictionary_item(Star, item_id)


@admin_router.post(
    "/directors",
    response_model=DirectorSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_director(
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.create_dictionary_item(Director, name)


@admin_router.patch("/directors/{item_id}", response_model=DirectorSchema)
async def update_director(
    item_id: int,
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.update_dictionary_item(Director, item_id, name)


@admin_router.delete(
    "/directors/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_director(
    item_id: int,
    service: MovieService = Depends(get_movie_service),
):
    await service.delete_dictionary_item(Director, item_id)


@admin_router.post(
    "/certifications",
    response_model=CertificationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_certification(
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.create_dictionary_item(Certification, name)


@admin_router.patch(
    "/certifications/{item_id}", response_model=CertificationSchema
)
async def update_certification(
    item_id: int,
    name: str,
    service: MovieService = Depends(get_movie_service),
):
    return await service.update_dictionary_item(Certification, item_id, name)


@admin_router.delete(
    "/certifications/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_certification(
    item_id: int,
    service: MovieService = Depends(get_movie_service),
):
    await service.delete_dictionary_item(Certification, item_id)


router.include_router(movies_router)
router.include_router(favorites_router)
router.include_router(genres_router)
router.include_router(admin_router)
