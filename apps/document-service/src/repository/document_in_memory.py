from typing import Optional, Dict
from uuid import UUID

from patterns.repository import AbstractRepository
from src.domains.documents.model import Document


class InMemoryDocumentRepository(AbstractRepository[Document]):
    def __init__(self) -> None:
        super().__init__()
        self._store: Dict[UUID, Document] = {}

    def _add(self, aggregate: Document) -> None:
        self._store[aggregate.id] = aggregate

    def _get(self, reference: UUID) -> Optional[Document]:
        return self._store.get(reference)

    def list_documents(self, skip: int = 0, limit: int = 50) -> list[Document]:
        values = list(self._store.values())
        return values[skip : skip + limit]

    def remove(self, document_id: UUID) -> None:
        self._store.pop(document_id, None)