from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import List
from enum import Enum
from patterns.aggregator import Aggregate
from src.config import settings
from src.dto.commands import (
    DocumentCreated,
    DocumentUpdated,
    DocumentDeleted,
    DocumentUploaded,
    DocumentParsed,
    EmbeddingsGenerated,
)


class State(Enum):
    CREATED = "created"
    UPLOADED = "uploaded"
    PARSED = "parsed"
    READY = "ready"



class Document(Aggregate):
    def __init__(
        self,
        *,
        document_id: UUID | None = None,
        title: str,
        file_name: str,
        author_id: UUID,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        state: State = State.CREATED,
    ) -> None:
        super().__init__()
        now = datetime.now(timezone.utc)
        self._id: UUID = document_id or uuid4()
        self._title: str = title
        self._file_name: str = file_name
        self._author_id: UUID = author_id
        self._created_at: datetime = created_at or now
        self._updated_at: datetime = updated_at or now
        self._state: State = state

    @classmethod
    def create(
        cls,
        *,
        title: str,
        file_name: str,
        author_id: UUID,
    ):
        document = cls(
            title=title,
            file_name=file_name,
            author_id=author_id,
            state=State.CREATED,
        )
        document._record_event(
            DocumentCreated(
                document_id=document.id,
                title=document.title,
                file_name=document.file_name,
                author_id=document.author_id,
            )
        )
        return document

    @classmethod
    def restore(
        cls,
        *,
        document_id: UUID,
        title: str,
        file_name: str,
        author_id: UUID,
        created_at: datetime,
        updated_at: datetime,
    ):
        return cls(
            document_id=document_id,
            title=title,
            file_name=file_name,
            author_id=author_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def id(self) -> UUID: return self._id

    @property
    def title(self) -> str: return self._title

    @property
    def file_name(self) -> str: return self._file_name

    @property
    def author_id(self) -> UUID: return self._author_id

    @property
    def created_at(self) -> datetime: return self._created_at

    @property
    def updated_at(self) -> datetime: return self._updated_at

    @property
    def state(self) -> State: return self._state


    def update_title(self, new_title: str) -> None:
        if not new_title:
            raise ValueError("Title should be non-empty")
        if new_title == self._title:
            return
        self._title = new_title
        self._touch()
        self._record_event(DocumentUpdated(document_id=self.id, changes={"title": new_title}))
    
    def mark_uploaded(self, file_size: int) -> None:
        if self._state != State.CREATED:
            raise ValueError("Can only upload from CREATED state")
        self._state = State.UPLOADED
        self._touch()
        self._record_event(DocumentUploaded(document_id=self.id, file_size=file_size))
    
    def mark_parsed(self, chunk_count: int) -> None:
        if self._state != State.UPLOADED:
            raise ValueError("Can only parse from UPLOADED state")
        self._state = State.PARSED
        self._touch()
        self._record_event(DocumentParsed(document_id=self.id, chunk_count=chunk_count))
    
    def mark_ready(self) -> None:
        if self._state != State.PARSED:
            raise ValueError("Can only mark ready from PARSED state")
        self._state = State.READY
        self._touch()
        self._record_event(EmbeddingsGenerated(document_id=self.id))
    
    def delete(self) -> None:
        self._record_event(DocumentDeleted(document_id=self.id))

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)


class Chunk(Aggregate):
    def __init__(
        self,
        *,
        chunk_id: UUID | None = None,
        document_id: UUID,
        content: str,
        embedding: List[float],
    ) -> None:
        super().__init__()
        self._id: UUID = chunk_id or uuid4()
        self._document_id: UUID = document_id
        self._content: str = content
        embedding_len = len(embedding)
        if embedding_len != settings.EMBEDDING_SIZE:
            raise ValueError(f"Expected embedding of size {settings.EMBEDDING_SIZE}, got {embedding_len}")
        self._embedding = embedding

    @classmethod
    def create(
        cls,
        *,
        document_id: UUID,
        content: str,
    ):
        chunk = cls(
            document_id=document_id,
            content=content,
        )
        return chunk

    @property
    def id(self) -> UUID: return self._id

    @property
    def document_id(self) -> UUID: return self._document_id

    @property
    def content(self) -> str: return self._content

    @property
    def embedding(self) -> List[float]: return self._embedding

