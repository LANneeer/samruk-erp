from dataclasses import dataclass
from patterns.message import Command, Event
from uuid import UUID
from typing import Any
from datetime import datetime

#############################################################################
#                                   COMMANDS                                #
#############################################################################

@dataclass(frozen=True, slots=True)
class CreateDocument(Command):
    document_id: UUID
    author_id: UUID
    title: str
    file_name: str

@dataclass(frozen=True, slots=True)
class UpdateDocument(Command):
    document_id: UUID
    title: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteDocument(Command):
    document_id: UUID


#############################################################################
#                                    EVENTS                                 #
#############################################################################

@dataclass(frozen=True, slots=True)
class DocumentCreated(Event):
    document_id: UUID
    created_at: datetime

@dataclass(frozen=True, slots=True)
class DocumentUpdated(Event):
    document_id: UUID
    updated_at: datetime
    changes: dict[str, Any]

@dataclass(frozen=True, slots=True)
class DocumentDeleted(Event):
    document_id: UUID
