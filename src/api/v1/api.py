from fastapi import APIRouter

from .admin.movies import router as admin_movies_router
from .orders import router as orders_router
from .payments import router as payments_router
from .users import router as users_router


api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(payments_router)
api_router.include_router(orders_router)
api_router.include_router(admin_movies_router)
