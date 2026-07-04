from fastapi import FastAPI

from api import api_v1_router
from core.config import settings


app = FastAPI()

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
