from dataclasses import dataclass
from typing import Any
from patterns.message import Event, Command

from uuid import UUID


@dataclass(frozen=True, slots=True)
class DocumentCreated(Event):
    document_id: UUID
    title: str
    file_name: str
    author_id: UUID


@dataclass(frozen=True, slots=True)
class DocumentUpdated(Event):
    document_id: UUID
    changes: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DocumentDeleted(Event):
    document_id: UUID


@dataclass(frozen=True, slots=True)
class CreateDocument(Command):
    title: str
    file_name: str
    author_id: UUID


@dataclass(frozen=True, slots=True)
class UpdateDocument(Command):
    document_id: UUID
    title: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteDocument(Command):
    document_id: UUID