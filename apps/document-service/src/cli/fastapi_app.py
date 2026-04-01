from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4
from logging import getLogger
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Query,
    UploadFile,
    File,
    Response,
)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from src.domains.documents.model import get_document_file_path
from src.gateway.schemas.documents import (
    DocumentReadDTO,
    DocumentUpdateDTO,
)
from src.dto.commands import (
    CreateDocument,
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

logger = getLogger("fastapi_app")

app = FastAPI(
    title="Document Service (async)", servers=[{"url": "/api/documents"}, {"url": "/"}]
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
install_exception_handlers(app)

settings.DOCUMENT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)



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
    items = await uow.documents.list_documents(skip=skip, limit=limit)
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


async def save_upload_file(upload_file: UploadFile) -> str:
    file_name = f"{uuid4().hex}-{Path(upload_file.filename).name}"
    file_path = get_document_file_path(file_name)
    logger.info(f"Saving uploaded file to '{file_path}'")
    with file_path.open("wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            f.write(chunk)
    return file_name


@app.post("/documents", response_model=DocumentReadDTO, status_code=status.HTTP_201_CREATED)
async def create_document(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    title: str,
    author_id: UUID,
    file: UploadFile = File(...),
):
    file_name = await save_upload_file(file)
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook)
    results = await bus.handle(
        CreateDocument(
            title=title,
            file_name=file_name,
            author_id=author_id,
        )
    )
    doc_id = results[0]
    doc = await uow.documents.get_async(doc_id)
    if not doc:
        raise HTTPException(status_code=500, detail="Document not persisted")
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
    doc = await uow.documents.get_async(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
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
    doc = await uow.documents.get_async(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in DB")
    file_path = get_document_file_path(doc.file_name)
    logger.info(f"Serving document file from '{file_path}'")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found in storage")
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
    doc = await uow.documents.get_async(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
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
    return None