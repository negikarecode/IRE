from celery import Celery
from app.config import settings

celery_app = Celery(
    "ire_tasks",
    broker=settings.assemble_celery_broker(),
    backend=settings.assemble_celery_broker()
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
