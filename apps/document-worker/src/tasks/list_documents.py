from celery import shared_task
import msgspec
from utils.domains.document.commands import ListDocuments
from utils.domains.document.gateway import DocumentDTO
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document
from src.infrastructure.asyncio_loop import await_sync

@shared_task(name="document-gateway.list_documents")
def list_documents(dto_json: str):
    cmd: ListDocuments = msgspec.json.decode(dto_json, type=ListDocuments)
    return msgspec.json.encode(await_sync(list_documents_async(cmd)))

async def list_documents_async(cmd: ListDocuments):
    async with AsyncUnitOfWork() as uow:
        items: list[Document] = await uow.documents.list_documents(skip=cmd.skip, limit=cmd.limit)
        return [
            DocumentDTO(
                id=d.id,
                title=d.title,
                file_name=d.file_name,
                author_id=d.author_id,
                created_at=d.created_at,
                updated_at=d.updated_at,
            ).model_dump()
            for d in items
        ]
