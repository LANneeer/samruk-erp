from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class DocumentCreateDTO(BaseModel):
    title: str = Field(min_length=1)
    content: str
    author_id: UUID

class DocumentReadDTO(BaseModel):
    id: UUID
    title: str
    content: str
    author_id: UUID
    created_at: datetime
    updated_at: datetime

class DocumentUpdateDTO(BaseModel):
    title: str | None = None
    content: str | None = None