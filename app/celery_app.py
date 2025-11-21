import os
from celery import Celery

BROKEN_URL = os.getenv("CELERY_BROKEN_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "worker",
    broker=BROKEN_URL,
    backend=BACKEND_URL,
    include=["app.tasks.processor"],
)

celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "main-queue"},
}
celery_app.conf.update(task_track_started=True)