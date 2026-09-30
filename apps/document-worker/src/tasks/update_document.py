from celery import shared_task
import msgspec
from utils.domains.document.commands import UpdateDocument, DocumentUpdated
from utils.domains.common.exceptions import NotFound
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document
from src.infrastructure.asyncio_loop import await_sync

@shared_task(name="document-gateway.update_document")
def update_document(dto_json: str):
    cmd: UpdateDocument = msgspec.json.decode(dto_json, type=UpdateDocument)
    return msgspec.json.encode(await_sync(update_document_async(cmd)))

async def update_document_async(cmd: UpdateDocument): 
    async with AsyncUnitOfWork() as uow:
        document: Document = await uow.documents.get_async(cmd.document_id)
        if not document:
            raise NotFound("Document not found")
        
        changes = dict()
        if cmd.title:
            document.update_title(cmd.title)
            changes.setdefault("title", cmd.title)
        await uow.documents.save(document)
        await uow.commit()

        return DocumentUpdated(
            document_id=document.id,
            updated_at=document.updated_at,
            changes=changes,
        ).model_dump()
