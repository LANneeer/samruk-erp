from uuid import UUID
from pathlib import Path
from typing import IO
import logging

logger = logging.getLogger("storage")
_document_storage_dir = None

def storage_init(document_storage_dir: Path):
    global _document_storage_dir
    _document_storage_dir = document_storage_dir
    _document_storage_dir.mkdir(parents=True, exist_ok=True)

def get_document_file_path(document_id: UUID) -> Path:
    return _document_storage_dir / str(document_id)

async def save_document_file(upload_file: IO[bytes], document_id: UUID) -> int:
    file_path = get_document_file_path(document_id)
    logger.info(f"Saving uploaded file to '{file_path}'")
    total_size = 0
    if file_path.exists():
        raise FileExistsError(f"trying save uploaded file, but file already exists at '{file_path}'")
    with file_path.open("wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            f.write(chunk)
            total_size += len(chunk)
    return total_size

def delete_document_file(document_id: UUID) -> None:
    file_path = get_document_file_path(document_id)
    logger.info(f"Deleting file '{file_path}'")
    file_path.unlink(missing_ok=True)
