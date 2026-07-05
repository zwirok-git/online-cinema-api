from fastapi import APIRouter

from .payments import router as payments_router
from .users import router as users_router


api_router = APIRouter()

api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(payments_router, tags=["Payments"])
