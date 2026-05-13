from typing import Tuple

from patterns.unit_of_work import AbstractUnitOfWork
from patterns.repository import AbstractRepository
from src.repository.document_in_memory import InMemoryDocumentRepository


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self.documents = InMemoryDocumentRepository()
        self.repositories: Tuple[AbstractRepository, ...] = (self.documents,)

    def __enter__(self) -> "InMemoryUnitOfWork":
        return super().__enter__()

    def _commit(self) -> None:
        pass

    def _rollback(self) -> None:
        self.documents.seen.clear()