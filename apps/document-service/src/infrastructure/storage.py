from fastapi import UploadFile
from uuid import UUID
from pathlib import Path
import logging
from src.config import settings

logger = logging.getLogger("storage")
settings.DOCUMENT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_document_file_path(document_id: UUID) -> Path:
    return settings.DOCUMENT_STORAGE_DIR / document_id.hex

async def save_document_file(upload_file: UploadFile, document_id: UUID) -> None:
    file_path = get_document_file_path(document_id)
    logger.info(f"Saving uploaded file to '{file_path}'")
    with file_path.open("wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            f.write(chunk)

def delete_document_file(document_id: UUID) -> None:
    file_path = get_document_file_path(document_id)
    logger.info(f"Deleting file '{file_path}' for document {document_id}")
    file_path.unlink(missing_ok=True)
