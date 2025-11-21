import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

BROKEN_URL = os.getenv("CELERY_BROKEN_URL")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND")

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