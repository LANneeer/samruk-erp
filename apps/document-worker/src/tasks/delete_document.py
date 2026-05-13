from src.celery_app import celery_app
import msgspec
from utils.domains.document.commands import DeleteDocument, DocumentDeleted
from utils.domains.common.exceptions import NotFound
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document

@celery_app.task(name="document-gateway.delete_document")
async def delete_document(kwargs: dict):
    cmd: DeleteDocument = msgspec.json.decode(kwargs['dto'], type=DeleteDocument)
    async with AsyncUnitOfWork() as uow:
        document: Document = await uow.documents.get_async(cmd.document_id)
        if not document:
            raise NotFound("Document not found")
        
        await uow.documents.remove(cmd.document_id)
        await uow.commit()

        return DocumentDeleted(
            document_id=cmd.document_id,
        )
