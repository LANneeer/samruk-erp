import logging
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import (
    FastAPI,
    Depends,
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
    DocumentReadDTO,
    DocumentUpdateDTO,
    ChunkDTO,
)
from utils.domains.document.commands import (
    CreateDocument, DocumentCreated,
    UpdateDocument, DocumentUpdated,
    DeleteDocument, DocumentDeleted,
)
from utils.infrastructure.idempotency_middleware import IdempotencyMiddleware
from utils.infrastructure.metrics_middleware import MetricsMiddleware, prom_endpoint
from utils.infrastructure.error import install_exception_handlers
from src.config import settings
from utils.infrastructure.logging import init_logging, get_request_id
import src.storage as storage
from celery import Celery
from celery.result import AsyncResult
import msgspec


# init other modules
init_logging(settings.LOG_LEVEL, settings.LOGSTASH_HOST, settings.LOGSTASH_PORT)
storage.storage_init()

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
    kwargs = { "dto": msgspec.json.encode(dto) }
    celery.send_task(task_name, kwargs=kwargs, task_id=task_id)
    return task_id


@app.get("/metrics")
def metrics():
    data, content_type = prom_endpoint()
    return Response(content=data, media_type=content_type)


@app.post("/documents", response_model=DocumentReadDTO, status_code=status.HTTP_201_CREATED)
async def create_document(
    title: str,
    author_id: UUID,
    upload_file: UploadFile = File(...),
):
    document_id = uuid4()
    temp_file_path = await storage.save_document_file(upload_file, document_id)
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
        logger.info(f"sent celery task '{task_id}'")
        
        #TODO: rewrite this route to return document_id immediately and add polling route to get document status
        logger.info(f"waiting for result of celery task '{task_id}'")
        async_result = AsyncResult(app=celery, task_id=task_id)
        result_str = async_result.get()
        task_result: DocumentCreated = msgspec.json.decode(result_str, type=DocumentCreated)

        storage.make_temp_document_file_persistent(temp_file_path, task_result.id)

        return DocumentReadDTO(
            id=task_result.document_id,
            title=task_result.title,
            file_name=task_result.file_name,
            author_id=task_result.author_id,
            created_at=task_result.created_at,
            updated_at=task_result.created_at,
        )
    except:
        storage.delete_document_file(document_id)
        raise

# @app.get("/documents", response_model=list[DocumentReadDTO])
# async def list_documents(
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
#     skip: int = Query(0, ge=0),
#     limit: int = Query(50, ge=1, le=200),
# ):
#     items: list[Document] = await uow.documents.list_documents(skip=skip, limit=limit)
#     return [
#         DocumentReadDTO(
#             id=d.id,
#             title=d.title,
#             file_name=d.file_name,
#             author_id=d.author_id,
#             created_at=d.created_at,
#             updated_at=d.updated_at,
#         )
#         for d in items
#     ]


# @app.get("/documents/{document_id}", response_model=DocumentReadDTO)
# async def get_document(
#     document_id: UUID,
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
# ):
#     doc: Document = await uow.documents.get_async(document_id)
#     if not doc:
#         raise NotFound("Document not found")
#     return DocumentReadDTO(
#         id=doc.id,
#         title=doc.title,
#         file_name=doc.file_name,
#         author_id=doc.author_id,
#         created_at=doc.created_at,
#         updated_at=doc.updated_at,
#     )


# @app.get("/documents/{document_id}/download", response_class=FileResponse)
# async def download_document(
#     document_id: UUID,
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
# ):
#     doc: Document = await uow.documents.get_async(document_id)
#     if not doc:
#         raise NotFound("Document not found in DB")
#     file_path = storage.get_document_file_path(document_id)
#     if not file_path.exists():
#         raise NotFound("Document file not found in storage")
#     return FileResponse(path=file_path, filename=doc.file_name, media_type='application/octet-stream')


# @app.patch("/documents/{document_id}", response_model=DocumentReadDTO)
# async def update_document(
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
#     document_id: UUID,
#     dto: DocumentUpdateDTO,
# ):
#     hook = PromAuditHook()
#     bus = bootstrap_async(uow, hook=hook)
#     await bus.handle(
#         UpdateDocument(document_id=document_id, title=dto.title)
#     )
#     doc: Document = await uow.documents.get_async(document_id)
#     if not doc:
#         raise NotFound("Document not found")
#     return DocumentReadDTO(
#         id=doc.id,
#         title=doc.title,
#         file_name=doc.file_name,
#         author_id=doc.author_id,
#         created_at=doc.created_at,
#         updated_at=doc.updated_at,
#     )


# @app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_document(
#     document_id: UUID,
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
# ):
#     hook = PromAuditHook()
#     bus = bootstrap_async(uow, hook=hook)
#     await bus.handle(DeleteDocument(document_id=document_id))
#     storage.delete_document_file(document_id)
#     return None


# @app.get("/documents/{document_id}/chunks", response_model=list[ChunkDTO])
# async def get_document_chunks(
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
#     document_id: UUID,
#     skip: int = Query(0, ge=0),
#     limit: int = Query(10, ge=1, le=20),
# ):
#     doc: Document = await uow.documents.get_async(document_id)
#     if not doc:
#         raise NotFound("Document not found")
    
#     chunks: list[Chunk] = await uow.documents.list_chunks(document_id, skip=skip, limit=limit)
#     if not chunks or len(chunks) == 0:
#         raise NotFound("Document chunks not found")

#     return [
#         ChunkDTO(
#             id=chunk.id,
#             document_id=chunk.document_id,
#             content=chunk.content,
#             embedding=chunk.embedding
#         )
#         for chunk in chunks
#     ]


# @app.get("/documents/{document_id}/chunks/search", response_model=list[ChunkDTO])
# async def document_vector_search(
#     uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
#     document_id: UUID,
#     query: str,
#     limit: int = Query(10, ge=1, le=20),
# ):
#     doc: Document = await uow.documents.get_async(document_id)
#     if not doc:
#         raise NotFound("Document not found")
    
#     embedder = MockEmbeddingGenerator() # TODO: replace with real embedding generator
#     query_embedding = await embedder.embed(query)
#     chunks: list[Chunk] = await uow.documents.vector_search(document_id, query_embedding=query_embedding, limit=limit)
#     if not chunks or len(chunks) == 0:
#         raise NotFound("Document chunks not found")

#     return [
#         ChunkDTO(
#             id=chunk.id,
#             document_id=chunk.document_id,
#             content=chunk.content,
#             embedding=chunk.embedding
#         )
#         for chunk in chunks
#     ]
