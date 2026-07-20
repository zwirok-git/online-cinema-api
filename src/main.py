from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin.setup import setup_admin
from api import api_v1_router
from api.exceptions import register_exception_handlers
from core.config import settings


app = FastAPI()

media_root = Path("media")
media_root.mkdir(exist_ok=True)

app.mount("/media", StaticFiles(directory=media_root), name="media")
setup_admin(app)

register_exception_handlers(app)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
