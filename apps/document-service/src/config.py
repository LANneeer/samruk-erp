from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    class Config:
        # load .env file from service root directory
        env_file = Path(__file__).resolve().parent.parent / ".env"
    
    APP_NAME: str = "documents-service"
    SERVICE_NAME: str = "document-service"
    PROM_ENABLED: bool = True

    DATABASE_URL: str # required
    DB_POOL_SIZE: int = 10
    DB_POOL_TIMEOUT: int = 30

    LOG_LEVEL: str = "INFO"
    LOGSTASH_HOST: str | None = None
    LOGSTASH_PORT: int = 5044
    TRACING_ENABLED: bool = False
    TRACING_ENDPOINT: str | None = None
    REQUEST_ID_HEADER: str = "X-Request-ID"

    REDIS_URL: str = "redis://localhost:6379/0"
    IDEMPOTENCY_TTL_SEC: int = 5
    IDEMPOTENCY_MAX_BODY_BYTES: int = 1048576 # 1 MB

    DOCUMENT_STORAGE_DIR: Path = Path("data/documents")
    DOCUMENT_CHUNK_ROWS: int = 30
    EMBEDDING_SIZE: int = 1536
    DOCUMENT_HNSW_EF_SEARCH: int = 200

settings = Settings()