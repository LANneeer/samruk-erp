from celery import shared_task
import msgspec
from utils.domains.document.commands import ChunkVectorSearch
from utils.domains.common.exceptions import NotFound
from utils.domains.document.gateway import ChunkDTO
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.domain.model import Document, Chunk
from src.infrastructure.embedding import MockEmbeddingGenerator #, OpenAIEmbeddingGenerator
from src.infrastructure.asyncio_loop import await_sync

@shared_task(name="document-gateway.chunk_vector_search")
def chunk_vector_search(dto_json: str):
    cmd: ChunkVectorSearch = msgspec.json.decode(dto_json, type=ChunkVectorSearch)
    return msgspec.json.encode(await_sync(chunk_vector_search_async(cmd)))

async def chunk_vector_search_async(cmd: ChunkVectorSearch):
    async with AsyncUnitOfWork() as uow:
        doc: Document = await uow.documents.get_async(cmd.document_id)
        if not doc:
            raise NotFound("Document not found")
        
        # TODO: replace with real embedding generator
        embedder = MockEmbeddingGenerator()
        query_embedding = await embedder.embed(cmd.query)
        chunks: list[Chunk] = await uow.documents.vector_search(cmd.document_id, query_embedding=query_embedding, limit=cmd.limit)
        if not chunks or len(chunks) == 0:
            raise NotFound("Document chunks not found")

        return [
            ChunkDTO(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
            ).model_dump()
            for chunk in chunks
        ]
