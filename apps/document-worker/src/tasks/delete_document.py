from celery import shared_task
import msgspec
from utils.domains.document.commands import DeleteDocument, DocumentDeleted
from utils.domains.common.exceptions import NotFound
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document
from src.infrastructure.asyncio_loop import await_sync

@shared_task(name="document-gateway.delete_document")
def delete_document(dto_json: str):
    cmd: DeleteDocument = msgspec.json.decode(dto_json, type=DeleteDocument)
    return msgspec.json.encode(await_sync(delete_document_async(cmd)))

async def delete_document_async(cmd: DeleteDocument):
    async with AsyncUnitOfWork() as uow:
        document: Document = await uow.documents.get_async(cmd.document_id)
        if not document:
            raise NotFound("Document not found")
        
        await uow.documents.remove(cmd.document_id)
        await uow.commit()

        return DocumentDeleted(
            document_id=cmd.document_id,
        ).model_dump()
