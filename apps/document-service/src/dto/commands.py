from dataclasses import dataclass
from typing import Any, List
from fastapi import UploadFile
from patterns.message import Event, Command
from uuid import UUID

@dataclass(frozen=True, slots=True)
class DocumentCreated(Event):
    document_id: UUID
    title: str
    file_name: str
    author_id: UUID

@dataclass(frozen=True, slots=True)
class DocumentUploaded(Event):
    document_id: UUID
    file_size: int

@dataclass(frozen=True, slots=True)
class DocumentParsed(Event):
    document_id: UUID
    chunk_count: int


@dataclass(frozen=True, slots=True)
class EmbeddingsGenerated(Event):
    document_id: UUID

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
class SaveDocumentUpload(Command):
    """Command to save the request body to storage"""
    doc: Any # cannot import Document here due to circular dependency
    upload_file: UploadFile

@dataclass(frozen=True, slots=True)
class ParseDocument(Command):
    """Command to parse the uploaded document and create chunks strings"""
    doc: Any

@dataclass(frozen=True, slots=True)
class GenerateEmbeddings(Command):
    """Command to generate embeddings for the document chunks ans save chunks as ChunkORM"""
    doc: Any
    chunks: List[str]

@dataclass(frozen=True, slots=True)
class UpdateDocument(Command):
    document_id: UUID
    title: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteDocument(Command):
    document_id: UUID
