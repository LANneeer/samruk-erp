from typing import Any, Protocol
from uuid import UUID

from utils.domains.common.exceptions import NotFound
from patterns.unit_of_work import AbstractUnitOfWork
from src.domains.documents.model import Document
from src.dto.commands import (
    CreateDocument,
    UpdateDocument,
    DeleteDocument,
    DocumentCreated,
    DocumentUpdated,
    DocumentDeleted,
)


class Notifier(Protocol):
    def send(self, *, channel: str, message: str) -> None: ...


class Publisher(Protocol):
    def publish(self, topic: str, payload: dict[str, Any]) -> None: ...


def handle_create_document(cmd: CreateDocument, uow: AbstractUnitOfWork) -> UUID:
    document = Document.create(
        title=cmd.title,
        file_name=cmd.file_name,
        author_id=cmd.author_id,
    )
    uow.documents.add(document)
    uow.commit()
    return document.id


def handle_update_document(cmd: UpdateDocument, uow: AbstractUnitOfWork) -> None:
    document = uow.documents.get(cmd.document_id)
    if document is None:
        raise NotFound("Document not found")

    if cmd.title:
        document.update_title(cmd.title)
    uow.documents.add(document)
    uow.commit()


def handle_delete_document(cmd: DeleteDocument, uow: AbstractUnitOfWork) -> None:
    document = uow.documents.get(cmd.document_id)
    if not document:
        raise NotFound("Document not found")

    document.delete()
    uow.documents.remove(cmd.document_id)
    uow.commit()


def on_document_created(evt: DocumentCreated, notifier: Notifier | None = None, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="document.created", payload={"document_id": str(evt.document_id), "title": evt.title})


def on_document_updated(evt: DocumentUpdated, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="document.updated", payload={"document_id": str(evt.document_id), "changes": evt.changes})


def on_document_deleted(evt: DocumentDeleted, publisher: Publisher | None = None) -> None:
    if publisher:
        publisher.publish(topic="document.deleted", payload={"document_id": str(evt.document_id)})