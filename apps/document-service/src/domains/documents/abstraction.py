from abc import ABC, abstractmethod
from typing import List, Optional
from src.domains.documents.model import Document

from uuid import UUID


class IDocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, document: Document) -> Document:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_documents(self, skip: int = 0, limit: int = 50) -> List[Document]:
        raise NotImplementedError