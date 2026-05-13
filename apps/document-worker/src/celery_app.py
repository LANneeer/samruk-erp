from celery import Celery
from src.config import settings
from utils.infrastructure.logging import init_logging


# init other modules
init_logging(settings.LOG_LEVEL, settings.LOGSTASH_HOST, settings.LOGSTASH_PORT)

# initialize celery
celery_app = Celery(
    "document_gateway",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Reliability settings
    # worker must report task completeness at the end, not at the beginning
    task_acks_late=True, 
    # explicitly requeues task if worker dies unexpectedly
    task_reject_on_worker_lost=True,
    # prevents one worker from hoarding many tasks
    worker_prefetch_multiplier=1,
)
celery_app.autodiscover_tasks([ "src.tasks" ])
