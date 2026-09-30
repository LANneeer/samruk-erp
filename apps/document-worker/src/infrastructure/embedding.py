from openai import AsyncOpenAI
from src.config import settings

class MockEmbeddingGenerator:
    async def embed(self, input: str) -> list[float]:
        # return a fixed-size embedding of zeros for testing
        return [0.0] * settings.EMBEDDING_SIZE

class OpenAIEmbeddingGenerator:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def embed(self, input: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=input)        
        embedding = response.data[0].embedding

        embedding_len = len(embedding)
        if embedding_len != settings.EMBEDDING_SIZE:
            raise ValueError(f"Expected embedding size {settings.EMBEDDING_SIZE}, got {embedding_len}")
        
        return embedding
