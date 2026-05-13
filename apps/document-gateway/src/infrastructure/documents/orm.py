from sqlalchemy import (
    Column,
    DateTime,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from src.infrastructure.db_async import DeclarativeBase
from src.config import settings

class DocumentORM(DeclarativeBase):
    __tablename__ = "documents"
    id = Column(PG_UUID, primary_key=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    author_id = Column(PG_UUID, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    __table_args__ = (
        Index("ix_documents_author_id", "author_id"),
    )


class ChunkORM(DeclarativeBase):
    __tablename__ = "chunks"
    id = Column(PG_UUID, primary_key=True)
    document_id = Column(PG_UUID, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_SIZE), nullable=False)
    __table_args__ = (
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_embedding", "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
