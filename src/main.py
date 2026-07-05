from fastapi import FastAPI

from api import api_v1_router
from api.exceptions import register_exception_handlers
from core.config import settings


app = FastAPI()

register_exception_handlers(app)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
