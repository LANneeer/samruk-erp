from src.celery_app import celery_app
import msgspec
from utils.domains.document.commands import CreateDocument, DocumentCreated
from utils.domains.common.exceptions import NotSupported
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document, Chunk
from src.infrastructure.parsing import Sheet, create_chunks_from_sheets_async
from src.infrastructure.embedding import MockEmbeddingGenerator #, OpenAIEmbeddingGenerator
import pandas as pd
from pathlib import Path

@celery_app.task(name="document-gateway.create_document")
async def create_document(kwargs: dict):
    cmd: CreateDocument = msgspec.json.decode(kwargs['dto'], type=CreateDocument)
    async with AsyncUnitOfWork() as uow:
        # create document model in memory
        document = Document.create(title=cmd.title, file_name=cmd.file_name, author_id=cmd.author_id)
        uow.documents.add(document)
        # recognize document type and split it into chunks
        str_chunks = await parse_document(document)
        # generate embeddings for chunks and save them in UOW
        await generate_embeddings(uow, document, str_chunks)
        # flush document and its chunks to database
        await uow.commit()
        
        return DocumentCreated(
            document_id=cmd.document_id,
            created_at=document.created_at,
        )


async def parse_document(document: Document):
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
    
    document.mark_parsed()
    return document_chunks


async def generate_embeddings(uow: AsyncUnitOfWork, document: Document, str_chunks: list[str]):
    # TODO: get openai token to use real embedding generator
    # embedding_generator = OpenAIEmbeddingGenerator()
    embedding_generator = MockEmbeddingGenerator()

    for chunk_content in str_chunks:
        embedding = await embedding_generator.embed(chunk_content)
        chunk = Chunk(document_id=document.id, content=chunk_content, embedding=embedding)
        uow.documents.add_chunk(chunk)

    document.mark_ready()
