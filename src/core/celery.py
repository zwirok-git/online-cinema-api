from celery import Celery


celery = Celery(
    "online_cinema",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]
