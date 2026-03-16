from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, Set, Any

from .aggregator import Aggregate


T = TypeVar("T", bound=Aggregate)


class AbstractRepository(Generic[T], ABC):
    """
    Repository - это слой между доменной логикой и базой данных
    - сохраняет агрегаты
    - достаёт агрегаты
    - изолирует доменную модель от ORM
    """

    def __init__(self) -> None:
        self.seen: Set[T] = set()

    @abstractmethod
    def _add(self, aggregate: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def _get(self, reference: Any) -> Optional[T]:
        raise NotImplementedError

    def add(self, aggregate: T) -> None:
        self._add(aggregate)
        self.seen.add(aggregate)

    def get(self, reference: Any) -> Optional[T]:
        agg = self._get(reference)
        if agg:
            self.seen.add(agg)
        return agg
