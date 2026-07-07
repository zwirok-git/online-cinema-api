from fastapi import APIRouter

from .movies import (
    certifications_router,
    directors_router,
    favorites_router,
    genres_router,
    movies_router,
    stars_router,
)
from .orders import router as orders_router
from .payments import router as payments_router
from .users import router as users_router


api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(payments_router)
api_router.include_router(orders_router)
api_router.include_router(movies_router)
api_router.include_router(favorites_router)
api_router.include_router(genres_router)
api_router.include_router(stars_router)
api_router.include_router(directors_router)
api_router.include_router(certifications_router)
