from celery import Celery

celery_app = Celery(
    "ro_tasks",
    broker="redis://redis:6379/0",  # Redis as the broker
    backend="redis://redis:6379/0",
)
