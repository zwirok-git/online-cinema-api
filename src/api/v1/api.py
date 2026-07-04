from fastapi import APIRouter

from .payments import router as payments_router


api_router = APIRouter()

api_router.include_router(payments_router, tags=["Payments"])
