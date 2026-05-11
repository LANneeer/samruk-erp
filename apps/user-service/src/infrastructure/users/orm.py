from enum import Enum
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from src.infrastructure.db_async import DeclarativeBase


class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"


class UserORM(DeclarativeBase):
    __tablename__ = "users"
    id = Column(PG_UUID, primary_key=True)
    email = Column(String(320), nullable=False, unique=True)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, server_default="user")
    locale = Column(String(16), nullable=False, server_default="en")
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
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
        CheckConstraint("length(username) >= 3", name="ck_users_username_len"),
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
    )
