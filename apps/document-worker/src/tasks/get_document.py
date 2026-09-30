from celery import shared_task
import msgspec
from utils.domains.document.commands import GetDocument
from utils.domains.document.gateway import DocumentDTO
from utils.domains.common.exceptions import NotFound
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document
from src.infrastructure.asyncio_loop import await_sync

@shared_task(name="document-gateway.get_document")
def get_document(dto_json: str):
    cmd: GetDocument = msgspec.json.decode(dto_json, type=GetDocument)
    return msgspec.json.encode(await_sync(get_document_async(cmd)))

async def get_document_async(cmd: GetDocument):
    async with AsyncUnitOfWork() as uow:
        doc: Document = await uow.documents.get_async(cmd.document_id)
        if not doc:
            raise NotFound("Document not found")
        return DocumentDTO(
            id=doc.id,
            title=doc.title,
            file_name=doc.file_name,
            author_id=doc.author_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        ).model_dump()