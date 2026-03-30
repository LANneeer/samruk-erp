from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from patterns.repository import AbstractRepository
from src.infrastructure.documents.orm import DocumentORM
from src.domains.documents.model import Document
from datetime import datetime, timezone


class SqlAlchemyAsyncDocumentRepository(AbstractRepository[Document]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.session = session

    def _add(self, aggregate: Document) -> None:
        self.session.add(self._to_orm(aggregate))

    def _get(self, reference: UUID) -> Optional[Document]:
        raise NotImplementedError("Use async method 'get_async'")

    async def save(self, aggregate: Document) -> Document:
        now = datetime.now(timezone.utc)

        orm_obj: Optional[DocumentORM] = await self.session.get(DocumentORM, aggregate.id)

        if orm_obj is None:
            orm_obj = self._to_orm(aggregate)
            if orm_obj.created_at is None:
                orm_obj.created_at = now
            orm_obj.updated_at = now
            self.session.add(orm_obj)
        else:
            orm_obj.title = aggregate.title
            orm_obj.content = aggregate.content
            orm_obj.author_id = aggregate.author_id
            orm_obj.updated_at = now

        return self._to_domain(orm_obj)

    async def get_async(self, document_id: UUID) -> Optional[Document]:
        row = await self.session.get(DocumentORM, document_id)
        return self._to_domain(row) if row else None

    async def list_documents(self, skip: int = 0, limit: int = 50) -> list[Document]:
        res = await self.session.execute(
            select(DocumentORM).order_by(DocumentORM.created_at.desc()).offset(skip).limit(limit)
        )
        rows: Sequence[DocumentORM] = res.scalars().all()
        return [self._to_domain(r) for r in rows]

    async def remove(self, document_id: UUID) -> None:
        await self.session.execute(delete(DocumentORM).where(DocumentORM.id == document_id))

    @staticmethod
    def _to_domain(row: DocumentORM) -> Document:
        return Document.restore(
            document_id=row.id,
            title=row.title,
            content=row.content,
            author_id=row.author_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_orm(agg: Document) -> DocumentORM:
        return DocumentORM(
            id=agg.id,
            title=agg.title,
            content=agg.content,
            author_id=agg.author_id,
            created_at=agg.created_at,
            updated_at=agg.updated_at,
        )