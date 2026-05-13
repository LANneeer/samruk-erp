from src.celery_app import celery_app
import msgspec
from utils.domains.document.commands import UpdateDocument, DocumentUpdated
from utils.domains.common.exceptions import NotFound
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document

@celery_app.task(name="document-gateway.update_document")
async def update_document(kwargs: dict):
    cmd: UpdateDocument = msgspec.json.decode(kwargs['dto'], type=UpdateDocument)
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
            document_id=document.document_id,
            updated_at=document.updated_at,
            changes=changes,
        )
