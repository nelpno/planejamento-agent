from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "planejamento_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.generation_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=600,  # 10 min max (planning takes longer than image gen)
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
)
