import logging
from uuid import UUID, uuid4
from fastapi import (
    FastAPI,
    status,
    Query,
    UploadFile,
    File,
    Response,
)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from utils.domains.common.exceptions import NotFound
from utils.domains.document.gateway import (
    DocumentDTO,
    UpdateDocumentDTO,
    DocumentUpdatedDTO,
    ChunkDTO,
)
from utils.domains.document.commands import (
    CreateDocument, DocumentCreated,
    UpdateDocument, DocumentUpdated,
    DeleteDocument, DocumentDeleted,
    GetDocument,
    ListDocuments,
    ChunkVectorSearch,
)
from utils.infrastructure.idempotency_middleware import IdempotencyMiddleware
from utils.infrastructure.metrics_middleware import MetricsMiddleware, prom_endpoint
from utils.infrastructure.error import install_exception_handlers
from src.config import settings
from utils.infrastructure.logging import init_logging, get_request_id
import utils.infrastructure.document.document_storage as document_storage
from celery import Celery
from celery.result import AsyncResult
import msgspec
from pydantic import TypeAdapter

# init other modules
init_logging(settings.LOG_LEVEL, settings.LOGSTASH_HOST, settings.LOGSTASH_PORT)
document_storage.storage_init(settings.DOCUMENT_STORAGE_DIR)

# initialize fastapi
app = FastAPI(
    title="Document Service", servers=[{"url": "/api/documents"}, {"url": "/"}]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(IdempotencyMiddleware, 
        redis_url=settings.REDIS_URL, 
        ttl_sec=settings.IDEMPOTENCY_TTL_SEC, 
        max_body_bytes=settings.IDEMPOTENCY_MAX_BODY_BYTES, 
        get_request_id=get_request_id,
    )
if settings.PROM_ENABLED:
    app.add_middleware(MetricsMiddleware)

# initialize logging
logger = logging.getLogger("app")
install_exception_handlers(app, logger)

# initialize celery
celery = Celery(
    "document_gateway",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery.conf.update(
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


def celery_send_task(task_name: str, dto) -> str:
    task_id=f"{task_name}:{uuid4()}"
    kwargs = { "dto_json": msgspec.json.encode(dto) }
    logger.info(f"sending celery task '{task_id}'")
    celery.send_task(task_name, kwargs=kwargs, task_id=task_id)
    return task_id

def celery_wait_task_result(task_id: str, result_type):
    logger.info(f"waiting for result of celery task '{task_id}'")
    async_result = AsyncResult(app=celery, id=task_id)
    result_str = async_result.get()
    logger.info(str(result_str))
    task_result = TypeAdapter(result_type).validate_json(result_str)
    return task_result

@app.get("/metrics")
def metrics():
    data, content_type = prom_endpoint()
    return Response(content=data, media_type=content_type)


@app.post("/documents", response_model=DocumentDTO, status_code=status.HTTP_201_CREATED)
async def create_document(
    title: str,
    author_id: UUID,
    upload_file: UploadFile = File(...),
):
    document_id = uuid4()
    temp_file_path = await document_storage.save_document_file(upload_file, document_id)
    # delete file if error
    try:
        task_id = celery_send_task("document-gateway.create_document", 
            CreateDocument(
                document_id=document_id,
                author_id=author_id,
                title=title,
                file_name=upload_file.filename,
            )
        )
        #TODO: rewrite this route to return document_id immediately and add polling route to get document status
        task_result: DocumentCreated = celery_wait_task_result(task_id, DocumentCreated)

        document_storage.make_temp_document_file_persistent(temp_file_path, task_result.id)

        return DocumentDTO(
            id=task_result.document_id,
            title=task_result.title,
            file_name=task_result.file_name,
            author_id=task_result.author_id,
            created_at=task_result.created_at,
            updated_at=task_result.created_at,
        )
    except:
        document_storage.delete_document_file(document_id)
        raise


@app.get("/documents/{document_id}", response_model=DocumentDTO)
async def get_document(
    document_id: UUID,
):
    task_id = celery_send_task("document-gateway.get_document", 
        GetDocument(
            document_id=document_id,
        )
    )
    task_result: DocumentDTO = celery_wait_task_result(task_id, DocumentDTO)
    return task_result


@app.get("/documents", response_model=list[DocumentDTO])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    task_id = celery_send_task("document-gateway.list_documents", 
        ListDocuments(
            skip=skip,
            limit=limit,
        )
    )
    task_result: list[DocumentDTO] = celery_wait_task_result(task_id, list[DocumentDTO])
    return task_result


@app.get("/documents/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: UUID,
):
    task_id = celery_send_task("document-gateway.get_document", 
        GetDocument(
            document_id=document_id,
        )
    )
    task_result: DocumentDTO = celery_wait_task_result(task_id, DocumentDTO)
    
    file_path = document_storage.get_document_file_path(document_id)
    if not file_path.exists():
        raise NotFound("Document file not found in storage")
    
    return FileResponse(
        path=file_path,
        filename=task_result.file_name,
        media_type='application/octet-stream'
    )


@app.patch("/documents/{document_id}", response_model=DocumentUpdatedDTO)
async def update_document(
    document_id: UUID,
    dto: UpdateDocumentDTO,
):
    task_id = celery_send_task("document-gateway.update_document", 
        UpdateDocument(
            document_id=document_id,
            title=dto.title
        )
    )
    task_result: DocumentUpdated = celery_wait_task_result(task_id, DocumentUpdated)
    return DocumentUpdatedDTO(
        updated_at=task_result.updated_at,
    )


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
):
    task_id = celery_send_task("document-gateway.delete_document", 
        DeleteDocument(
            document_id=document_id,
        )
    )
    celery_wait_task_result(task_id, DocumentDeleted)

    document_storage.delete_document_file(document_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/documents/{document_id}/chunks/search", response_model=list[ChunkDTO])
async def chunk_vector_search(
    document_id: UUID,
    query: str,
    limit: int = Query(10, ge=1, le=20),
):
    task_id = celery_send_task("document-gateway.chunk_vector_search", 
        ChunkVectorSearch(
            document_id=document_id,
            query=query,
            limit=limit,
        )
    )
    task_result: list[ChunkDTO] = celery_wait_task_result(task_id, list[ChunkDTO])
    return task_result
