from datetime import datetime, timezone
import logging
from uuid import UUID, uuid4
from pathlib import Path
from patterns.aggregator import Aggregate

from src.dto.commands import (
    DocumentCreated,
    DocumentUpdated,
    DocumentDeleted,
)
from src.config import settings

logger = logging.getLogger("document")

def get_document_file_path(file_name) -> Path:
    return settings.DOCUMENT_STORAGE_DIR / file_name

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
    ) -> None:
        super().__init__()
        now = datetime.now(timezone.utc)
        self._id: UUID = document_id or uuid4()
        self._title: str = title
        self._file_name: str = file_name
        self._author_id: UUID = author_id
        self._created_at: datetime = created_at or now
        self._updated_at: datetime = updated_at or now

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


    def update_title(self, new_title: str) -> None:
        if not new_title:
            raise ValueError("Title should be non-empty")
        if new_title == self._title:
            return
        self._title = new_title
        self._touch()
        self._record_event(DocumentUpdated(document_id=self.id, changes={"title": new_title}))
    
    def delete(self) -> None:
        file_path = get_document_file_path(self.file_name)
        logger.info(f"Deleting file '{file_path}' for document {self.id}")
        file_path.unlink(missing_ok=True)
        self._record_event(DocumentDeleted(document_id=self.id))

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)