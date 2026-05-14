from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
#
# These classes are converted to json automatically by fastapi
#

class DocumentDTO(BaseModel):
    id: UUID
    title: str
    file_name: str
    author_id: UUID
    created_at: datetime
    updated_at: datetime

class UpdateDocumentDTO(BaseModel):
    title: str | None = None

class DocumentUpdatedDTO(BaseModel):
    updated_at: datetime

class ChunkDTO(BaseModel):
    id: UUID
    document_id: UUID
    content: str
