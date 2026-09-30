from celery import Celery
from src.config import settings
from utils.infrastructure.logging import init_logging
import utils.infrastructure.document.document_storage as document_storage
from src.infrastructure.asyncio_loop import init_main_loop
from src.tasks.chunk_vector_search import *
from src.tasks.create_document import *
from src.tasks.delete_document import *
from src.tasks.get_document import *
from src.tasks.list_documents import *
from src.tasks.update_document import *

# init other modules
init_logging(settings.LOG_LEVEL, settings.LOGSTASH_HOST, settings.LOGSTASH_PORT)
document_storage.storage_init(settings.DOCUMENT_STORAGE_DIR)
# fix some weird "loop reuse" which leads to UoW newer close and DB connection pool breaks
init_main_loop()

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
