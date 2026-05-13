from typing import Optional, Dict, List
from uuid import UUID
from patterns.repository import AbstractRepository
from src.domains.documents.model import Document, Chunk
from src.config import settings


class InMemoryDocumentRepository(AbstractRepository[Document]):
    def __init__(self) -> None:
        super().__init__()
        self._store: Dict[UUID, Document] = {}
        self._chunks: Dict[UUID, List[Chunk]] = {}

    def _add(self, aggregate: Document) -> None:
        self._store[aggregate.id] = aggregate

    def _get(self, reference: UUID) -> Optional[Document]:
        return self._store.get(reference)

    def list_documents(self, skip: int = 0, limit: int = 50) -> list[Document]:
        values = list(self._store.values())
        return values[skip : skip + limit]

    def add_chunk(self, chunk: Chunk) -> None:
        self._chunks.setdefault(chunk.document_id, []).append(chunk)

    def list_chunks(self, document_id: UUID) -> list[Chunk]:
        return list(self._chunks.get(document_id, []))

    async def vector_search(self, document_id: UUID, query_embedding: List[float], limit: int = 10) -> list[Chunk]:
        if len(query_embedding) != settings.EMBEDDING_SIZE:
            raise ValueError(f"Query embedding must be of size {settings.EMBEDDING_SIZE}")
        
        # Simple linear search for demonstration purposes
        def distance(chunk: Chunk) -> float:
            if chunk.embedding is None:
                return float("inf")
            return sum((a - b) ** 2 for a, b in zip(chunk.embedding, query_embedding))

        all_chunks = self._chunks.get(document_id)
        if not all_chunks:
            raise ValueError("Document not found or has no chunks")
        all_chunks.sort(key=distance)
        return all_chunks[:limit]

    def remove(self, document_id: UUID) -> None:
        self._store.pop(document_id, None)
        self._chunks.pop(document_id, None)