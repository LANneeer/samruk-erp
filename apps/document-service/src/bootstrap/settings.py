from typing import Sequence, Mapping, Type

from patterns.message_bus import MessageBus
from patterns.message import Command, Event
from patterns.unit_of_work import AbstractUnitOfWork

from src.dto.commands import (
    CreateDocument,
    UpdateDocument,
    DeleteDocument,
)
from src.gateway.handlers.document import (
    handle_create_document,
    handle_update_document,
    handle_delete_document,
    on_document_created,
    on_document_updated,
    on_document_deleted,
)
from src.dto.commands import (
    DocumentCreated,
    DocumentUpdated,
    DocumentDeleted,
)


def bootstrap(uow: AbstractUnitOfWork, **deps) -> MessageBus:
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

    bus = MessageBus(
        uow=uow,
        event_handlers=event_handlers,
        command_handlers=command_handlers,
        dependencies=deps,
        raise_on_error=True,
    )
    return bus