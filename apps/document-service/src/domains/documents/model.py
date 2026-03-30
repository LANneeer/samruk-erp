from datetime import datetime, timezone
from uuid import UUID, uuid4
from patterns.aggregator import Aggregate

from src.dto.commands import (
    DocumentCreated,
    DocumentUpdated,
    DocumentDeleted,
)


class Document(Aggregate):
    def __init__(
        self,
        *,
        document_id: UUID | None = None,
        title: str,
        content: str,
        author_id: UUID,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__()
        now = datetime.now(timezone.utc)
        self._id: UUID = document_id or uuid4()
        self._title: str = title
        self._content: str = content
        self._author_id: UUID = author_id
        self._created_at: datetime = created_at or now
        self._updated_at: datetime = updated_at or now

    @classmethod
    def create(
        cls,
        *,
        title: str,
        content: str,
        author_id: UUID,
    ):
        document = cls(
            title=title,
            content=content,
            author_id=author_id,
        )
        document._record_event(
            DocumentCreated(
                document_id=document.id,
                title=document.title,
                content=document.content,
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
        content: str,
        author_id: UUID,
        created_at: datetime,
        updated_at: datetime,
    ):
        return cls(
            document_id=document_id,
            title=title,
            content=content,
            author_id=author_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def id(self) -> UUID: return self._id

    @property
    def title(self) -> str: return self._title

    @property
    def content(self) -> str: return self._content

    @property
    def author_id(self) -> UUID: return self._author_id

    @property
    def created_at(self) -> datetime: return self._created_at

    @property
    def updated_at(self) -> datetime: return self._updated_at

    def update_title(self, new_title: str) -> None:
        if not new_title:
            raise ValueError("Title should be non-empty")
        if new_title == self._title:
            return
        self._title = new_title
        self._touch()
        self._record_event(DocumentUpdated(document_id=self.id, changes={"title": new_title}))

    def update_content(self, new_content: str) -> None:
        if new_content == self._content:
            return
        self._content = new_content
        self._touch()
        self._record_event(DocumentUpdated(document_id=self.id, changes={"content": new_content}))

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)