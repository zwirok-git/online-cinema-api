from celery import Celery
from celery.schedules import crontab

from core.config import settings


celery = Celery(
    "online_cinema",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.tokens", "tasks.send_email"],
)

celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]
celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {
    "cleanup_expired_tokens": {
        "task": "delete_expired_tokens",
        "schedule": crontab(minute="0", hour="0"),
    }
}
