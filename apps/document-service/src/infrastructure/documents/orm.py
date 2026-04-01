from sqlalchemy import (
    Column,
    DateTime,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from src.infrastructure.db_async import DeclarativeBase


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