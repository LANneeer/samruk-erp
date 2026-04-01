from typing import Any, Protocol
from uuid import UUID
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from src.domains.documents.model import Document, DocumentCreated, DocumentUpdated, DocumentDeleted
from src.dto.commands import CreateDocument, UpdateDocument, DeleteDocument
from utils.domains.common.exceptions import NotFound

class Notifier(Protocol):
    async def send(self, *, channel: str, message: str) -> None: ...

class Publisher(Protocol):
    async def publish(self, topic: str, payload: dict[str, Any]) -> None: ...

async def handle_create_document(cmd: CreateDocument, uow: AsyncAbstractUnitOfWork) -> UUID:
    document = Document.create(title=cmd.title, file_name=cmd.file_name, author_id=cmd.author_id)
    uow.documents.add(document)
    await uow.commit()
    return document.id

async def handle_update_document(cmd: UpdateDocument, uow: AsyncAbstractUnitOfWork) -> None:
    document = await uow.documents.get_async(cmd.document_id)
    if not document:
        raise NotFound("Document not found")
    
    if cmd.title:
        document.update_title(cmd.title)
    await uow.documents.save(document)
    await uow.commit()

async def handle_delete_document(cmd: DeleteDocument, uow: AsyncAbstractUnitOfWork) -> None:
    document = await uow.documents.get_async(cmd.document_id)
    if not document:
        raise NotFound("Document not found")
    
    document.delete()
    await uow.documents.delete(cmd.document_id)
    await uow.commit()

async def on_document_created(evt: DocumentCreated, notifier: Notifier | None = None, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.created", payload={"document_id": str(evt.document_id), "title": evt.title})

async def on_document_updated(evt: DocumentUpdated, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.updated", payload={"document_id": str(evt.document_id), "changes": evt.changes})


async def on_document_deleted(evt: DocumentDeleted, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.deleted", payload={"document_id": str(evt.document_id)})