from typing import Mapping, Sequence, Type
from patterns.message import Command, Event
from patterns.message_bus import AsyncMessageBus
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from patterns.observability import ObservabilityHook
from src.dto.commands import (
    CreateDocument,
    UpdateDocument,
    DeleteDocument,
)
from src.dto.commands import (
    DocumentCreated,
    DocumentUpdated,
    DocumentDeleted,
)
from src.gateway.handlers.async_document import (
    handle_create_document, handle_update_document, handle_delete_document,
    on_document_created, on_document_updated, on_document_deleted
)


def bootstrap_async(uow: AsyncAbstractUnitOfWork, hook: ObservabilityHook | None = None, **deps) -> AsyncMessageBus:
    event_handlers: Mapping[Type[Event], Sequence] = {
        DocumentCreated: [on_document_created],
        DocumentUpdated: [on_document_updated],
        DocumentDeleted: [on_document_deleted],
    }
    command_handlers: Mapping[Type[Command], callable] = {
        CreateDocument: handle_create_document,
        UpdateDocument: handle_update_document,
        DeleteDocument: handle_delete_document,
    }
    return AsyncMessageBus(
        uow=uow,
        event_handlers=event_handlers,
        command_handlers=command_handlers,
        dependencies=deps,
        raise_on_error=True,
        hook=hook
    )