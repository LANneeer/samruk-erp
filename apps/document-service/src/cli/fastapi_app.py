import logging
from typing import Annotated
from uuid import UUID
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
from utils.domains.common.exceptions import DomainError, NotFound
from src.domains.documents.model import Document, Chunk
from src.gateway.schemas.documents import (
    DocumentReadDTO,
    DocumentUpdateDTO,
    ChunkDTO,
)
from src.dto.commands import (
    CreateDocument,
    SaveDocumentUpload,
    ParseDocument,
    GenerateEmbeddings,
    UpdateDocument,
    DeleteDocument,
)
from src.bootstrap.async_settings import bootstrap_async
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.infrastructure.hooks import PromAuditHook
from utils.infrastructure.idempotency_middleware import IdempotencyMiddleware
from utils.infrastructure.metrics_middleware import MetricsMiddleware, prom_endpoint
from utils.infrastructure.error import install_exception_handlers
from src.config import settings
from src.infrastructure.logging import get_request_id
from src.infrastructure.storage import delete_document_file, get_document_file_path


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
logger = logging.getLogger("app")
install_exception_handlers(app, logger)


async def get_uow():
    async with AsyncUnitOfWork() as uow:
        yield uow

@app.get("/metrics")
def metrics():
    data, content_type = prom_endpoint()
    return Response(content=data, media_type=content_type)


@app.get("/documents", response_model=list[DocumentReadDTO])
async def list_documents(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items: list[Document] = await uow.documents.list_documents(skip=skip, limit=limit)
    return [
        DocumentReadDTO(
            id=d.id,
            title=d.title,
            file_name=d.file_name,
            author_id=d.author_id,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in items
    ]


@app.post("/documents", response_model=DocumentReadDTO, status_code=status.HTTP_201_CREATED)
async def create_document(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    title: str,
    author_id: UUID,
    file: UploadFile = File(...),
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)

    results = await bus.handle(
        CreateDocument(
            title=title,
            file_name=file.filename,
            author_id=author_id,
        )
    )
    doc: Document = results[0]
    
    await bus.handle(SaveDocumentUpload(doc=doc, upload_file=file))

    results = await bus.handle(ParseDocument(doc=doc))
    chunked_content: list[str] = results[0]
    
    await bus.handle(GenerateEmbeddings(doc=doc, chunks=chunked_content))

    return DocumentReadDTO(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        author_id=doc.author_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@app.get("/documents/{document_id}", response_model=DocumentReadDTO)
async def get_document(
    document_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    doc: Document = await uow.documents.get_async(document_id)
    if not doc:
        raise NotFound("Document not found")
    return DocumentReadDTO(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        author_id=doc.author_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@app.get("/documents/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    doc: Document = await uow.documents.get_async(document_id)
    if not doc:
        raise NotFound("Document not found in DB")
    file_path = get_document_file_path(document_id)
    if not file_path.exists():
        raise NotFound("Document file not found in storage")
    return FileResponse(path=file_path, filename=doc.file_name, media_type='application/octet-stream')


@app.patch("/documents/{document_id}", response_model=DocumentReadDTO)
async def update_document(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    document_id: UUID,
    dto: DocumentUpdateDTO,
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    await bus.handle(
        UpdateDocument(document_id=document_id, title=dto.title)
    )
    doc: Document = await uow.documents.get_async(document_id)
    if not doc:
        raise NotFound("Document not found")
    return DocumentReadDTO(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        author_id=doc.author_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    await bus.handle(DeleteDocument(document_id=document_id))
    delete_document_file(document_id)
    return None


@app.get("/documents/{document_id}/chunks", response_model=list[ChunkDTO])
async def get_document_chunks(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    document_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=20),
):
    doc: Document = await uow.documents.get_async(document_id)
    if not doc:
        raise NotFound("Document not found")
    
    chunks: list[Chunk] = await uow.documents.list_chunks(document_id, skip=skip, limit=limit)
    if not chunks or len(chunks) == 0:
        raise NotFound("Document chunks not found")

    return [
        ChunkDTO(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=chunk.embedding
        )
        for chunk in chunks
    ]

@app.get("/documents/{document_id}/chunks/search", response_model=list[ChunkDTO])

async def document_vector_search(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    document_id: UUID,
    limit: int = Query(10, ge=1, le=20),
):
    doc: Document = await uow.documents.get_async(document_id)
    if not doc:
        raise NotFound("Document not found")
    
    chunks: list[Chunk] = await uow.documents.vector_search(document_id, limit=limit)
    if not chunks or len(chunks) == 0:
        raise NotFound("Document chunks not found")

    return [
        ChunkDTO(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=chunk.embedding
        )
        for chunk in chunks
    ]
