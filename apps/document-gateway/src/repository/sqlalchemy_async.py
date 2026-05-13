from typing import Optional, Sequence, List
from uuid import UUID
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from patterns.repository import AbstractRepository
from src.infrastructure.documents.orm import DocumentORM, ChunkORM
from src.config import settings
from src.domains.documents.model import Document, Chunk
from datetime import datetime, timezone


class SqlAlchemyAsyncDocumentRepository(AbstractRepository[Document]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.session = session

    def _add(self, aggregate: Document) -> None:
        self.session.add(self._document_to_orm(aggregate))

    def _get(self, reference: UUID) -> Optional[Document]:
        raise NotImplementedError("Use async method 'get_async'")

    async def save(self, aggregate: Document) -> Document:
        now = datetime.now(timezone.utc)

        orm_obj: Optional[DocumentORM] = await self.session.get(DocumentORM, aggregate.id)

        if orm_obj is None:
            orm_obj = self._document_to_orm(aggregate)
            if orm_obj.created_at is None:
                orm_obj.created_at = now
            orm_obj.updated_at = now
            self.session.add(orm_obj)
        else:
            orm_obj.title = aggregate.title
            orm_obj.file_name = aggregate.file_name
            orm_obj.author_id = aggregate.author_id
            orm_obj.updated_at = now

        return self._document_to_domain(orm_obj)

    async def get_async(self, document_id: UUID) -> Optional[Document]:
        row = await self.session.get(DocumentORM, document_id)
        return self._document_to_domain(row) if row else None

    def add_chunk(self, chunk: Chunk) -> None:
        self.session.add(self._chunk_to_orm(chunk))

    async def list_chunks(self, document_id: UUID, skip: int = 0, limit: int = 10) -> list[Chunk]:
        result = await self.session.execute(
            select(ChunkORM)
            .where(ChunkORM.document_id == document_id)
            .offset(skip)
            .limit(limit)
        )
        rows: Sequence[ChunkORM] = result.scalars().all()
        return [self._chunk_to_domain(row) for row in rows]

    async def vector_search(self, document_id: UUID, query_embedding: List[float], limit: int = 10) -> list[Chunk]:
        if len(query_embedding) != settings.EMBEDDING_SIZE:
            raise ValueError(f"Query embedding must be of size {settings.EMBEDDING_SIZE}")
        # How many candidate nodes to explore during search
        await self.session.execute(text(f"SET hnsw.ef_search = {settings.DOCUMENT_HNSW_EF_SEARCH}"))
        result = await self.session.execute(
            select(ChunkORM)
            .where(ChunkORM.document_id == document_id)
            .where(ChunkORM.embedding.isnot(None))
            .order_by(ChunkORM.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        rows: Sequence[ChunkORM] = result.scalars().all()
        return [self._chunk_to_domain(row) for row in rows]

    async def list_documents(self, skip: int = 0, limit: int = 50) -> list[Document]:
        res = await self.session.execute(
            select(DocumentORM).order_by(DocumentORM.created_at.desc()).offset(skip).limit(limit)
        )
        rows: Sequence[DocumentORM] = res.scalars().all()
        return [self._document_to_domain(r) for r in rows]

    async def remove(self, document_id: UUID) -> None:
        await self.session.execute(delete(ChunkORM).where(ChunkORM.document_id == document_id))
        await self.session.execute(delete(DocumentORM).where(DocumentORM.id == document_id))

    @staticmethod
    def _document_to_domain(row: DocumentORM) -> Document:
        return Document.restore(
            document_id=row.id,
            title=row.title,
            file_name=row.file_name,
            author_id=row.author_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _document_to_orm(agg: Document) -> DocumentORM:
        return DocumentORM(
            id=agg.id,
            title=agg.title,
            file_name=agg.file_name,
            author_id=agg.author_id,
            created_at=agg.created_at,
            updated_at=agg.updated_at,
        )

    @staticmethod
    def _chunk_to_domain(row: ChunkORM) -> Chunk:
        return Chunk(
            chunk_id=row.id,
            document_id=row.document_id,
            content=row.content,
            embedding=row.embedding,
        )

    @staticmethod
    def _chunk_to_orm(chunk: Chunk) -> ChunkORM:
        return ChunkORM(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=chunk.embedding,
        )
