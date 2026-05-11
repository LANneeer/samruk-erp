from typing import Any, Protocol
from uuid import UUID
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from src.domains.documents.model import Document, Chunk
from src.dto.commands import (
    CreateDocument,
    SaveDocumentUpload,
    ParseDocument,
    GenerateEmbeddings,
    UpdateDocument,
    DeleteDocument,
)
from src.dto.commands import (
    DocumentCreated,
    DocumentUploaded,
    DocumentParsed,
    EmbeddingsGenerated,
    DocumentUpdated,
    DocumentDeleted,
)
from src.infrastructure.storage import save_document_file, get_document_file_path
from utils.domains.common.exceptions import NotFound, NotSupported
import pandas as pd
from pathlib import Path
from src.infrastructure.documents.embedding import MockEmbeddingGenerator, OpenAIEmbeddingGenerator
from src.infrastructure.documents.parsing import Sheet, create_chunks_from_sheets_async

class Notifier(Protocol):
    async def send(self, *, channel: str, message: str) -> None: ...

class Publisher(Protocol):
    async def publish(self, topic: str, payload: dict[str, Any]) -> None: ...



async def handle_create_document(cmd: CreateDocument, uow: AsyncAbstractUnitOfWork) -> UUID:
    document = Document.create(title=cmd.title, file_name=cmd.file_name, author_id=cmd.author_id)
    uow.documents.add(document)
    return document


async def handle_save_document_upload(cmd: SaveDocumentUpload, uow: AsyncAbstractUnitOfWork) -> None:
    document: Document = cmd.doc
    file_size = await save_document_file(cmd.upload_file, document.id)
    document.mark_uploaded(file_size)


async def handle_parse_document(cmd: ParseDocument, uow: AsyncAbstractUnitOfWork) -> None:
    document: Document = cmd.doc
    original_file_name = Path(document.file_name)
    ext = original_file_name.suffix.lower()
    file_path = get_document_file_path(document.id)

    sheets: list[Sheet] = []
    # parse different file types as Sheet objects
    if ext == ".csv":
        df: pd.DataFrame = pd.read_csv(file_path)
        sheets.append(Sheet(name=original_file_name.stem, columns=df.columns.tolist(), df=df))
    elif ext in [".xls", ".xlsx", ".xlsm", ".xlsb", ".odf", ".ods", ".odt"]:
        all_sheets: dict[str | int, pd.DataFrame] = pd.read_excel(file_path, sheet_name=None)
        for sheet_name, df in all_sheets.items():
            sheets.append(Sheet(name=str(sheet_name), columns=df.columns.tolist(), df=df))
    else:
        raise NotSupported(f"Unsupported file type: {ext}")
    
    # create chunks for all sheets in parallel threads
    document_chunks: list[str] = await create_chunks_from_sheets_async(sheets)
    
    document.mark_parsed(len(document_chunks))
    return document_chunks


async def handle_generate_embeddings(cmd: GenerateEmbeddings, uow: AsyncAbstractUnitOfWork) -> None:
    document: Document = cmd.doc
    # TODO: get openai token
    # embedding_generator = OpenAIEmbeddingGenerator()
    embedding_generator = MockEmbeddingGenerator()

    for chunk_content in cmd.chunks:
        embedding = await embedding_generator.embed(chunk_content)
        chunk = Chunk(document_id=document.id, content=chunk_content, embedding=embedding)
        uow.documents.add_chunk(chunk)

    document.mark_ready()
    # Save document and its chunks to database
    await uow.commit()


async def handle_update_document(cmd: UpdateDocument, uow: AsyncAbstractUnitOfWork) -> None:
    document = await uow.documents.get_async(cmd.document_id)
    if not document:
        raise NotFound("Document not found")
    
    if cmd.title:
        document.update_title(cmd.title)
    await uow.documents.save(document)
    await uow.commit()


async def handle_delete_document(cmd: DeleteDocument, uow: AsyncAbstractUnitOfWork) -> None:
    document = await uow.documents.get_async(cmd.document_id)
    if not document:
        raise NotFound("Document not found")
    
    document.delete()
    await uow.documents.remove(cmd.document_id)
    await uow.commit()



async def on_document_created(evt: DocumentCreated, notifier: Notifier | None = None, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.created", payload={
            "document_id": str(evt.document_id), 
            "title": evt.title
        })


async def on_document_uploaded(evt: DocumentUploaded, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.uploaded", payload={
            "document_id": str(evt.document_id),
            "file_size": str(evt.file_size)
        })


async def on_document_parsed(evt: DocumentParsed, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.parsed", payload={
            "document_id": str(evt.document_id),
            "chunk_count": str(evt.chunk_count)
        })


async def on_embeddings_generated(evt: EmbeddingsGenerated, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="embeddings.generated", payload={
            "document_id": str(evt.document_id)
        })


async def on_document_updated(evt: DocumentUpdated, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.updated", payload={
            "document_id": str(evt.document_id), 
            "changes": str(evt.changes)
        })


async def on_document_deleted(evt: DocumentDeleted, publisher: Publisher | None = None) -> None:
    if publisher:
        await publisher.publish(topic="document.deleted", payload={
            "document_id": str(evt.document_id)
        })
