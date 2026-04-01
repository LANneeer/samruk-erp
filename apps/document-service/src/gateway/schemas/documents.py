from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class DocumentReadDTO(BaseModel):
    id: UUID
    title: str
    file_name: str
    author_id: UUID
    created_at: datetime
    updated_at: datetime

class DocumentUpdateDTO(BaseModel):
    title: str | None = None