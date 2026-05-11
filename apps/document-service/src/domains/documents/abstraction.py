from abc import ABC, abstractmethod
from typing import List, Optional
from src.domains.documents.model import Document, Chunk

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

    @abstractmethod
    def add_chunk(self, chunk: Chunk) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_chunks(self, document_id: UUID) -> List[Chunk]:
        raise NotImplementedError

    @abstractmethod
    async def vector_search(self, document_id: UUID, query_embedding: List[float], limit: int = 10) -> List[Chunk]:
        raise NotImplementedError