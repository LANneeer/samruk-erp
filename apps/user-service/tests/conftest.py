from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVICE_ROOT.parents[1]

for path in (
    SERVICE_ROOT,
    REPO_ROOT / "packages" / "patterns",
):
    sys.path.insert(0, str(path))


from patterns.repository import AbstractRepository
from patterns.unit_of_work import AsyncAbstractUnitOfWork
from src.domains.users.model import User


class AsyncInMemoryUserRepository(AbstractRepository[User]):
    def __init__(self, users: list[User] | None = None) -> None:
        super().__init__()
        self._store: dict[UUID, User] = {}
        for user in users or []:
            self._store[user.id] = user

    def _add(self, aggregate: User) -> None:
        self._store[aggregate.id] = aggregate

    def _get(self, reference: UUID) -> User | None:
        return self._store.get(reference)

    async def get_async(self, user_id: UUID) -> User | None:
        user = self._get(user_id)
        if user:
            self.seen.add(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        user = next((u for u in self._store.values() if u.email == email), None)
        if user:
            self.seen.add(user)
        return user

    async def get_by_username(self, username: str) -> User | None:
        user = next((u for u in self._store.values() if u.username == username), None)
        if user:
            self.seen.add(user)
        return user

    async def list_users(self, skip: int = 0, limit: int = 50) -> list[User]:
        return list(self._store.values())[skip : skip + limit]

    async def save(self, user: User) -> User:
        self._store[user.id] = user
        self.seen.add(user)
        return user

    async def remove(self, user_id: UUID) -> None:
        self._store.pop(user_id, None)


class FakeAsyncUnitOfWork(AsyncAbstractUnitOfWork):
    def __init__(self, users: AsyncInMemoryUserRepository | None = None) -> None:
        super().__init__()
        self.users = users or AsyncInMemoryUserRepository()
        self.repositories = (self.users,)
        self.commits = 0
        self.rollbacks = 0

    async def _commit(self) -> None:
        self.commits += 1

    async def _rollback(self) -> None:
        self.rollbacks += 1


class RecordingHook:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    async def on_command_start(self, cmd: Any) -> None:
        self.calls.append(("command_start", type(cmd).__name__))

    async def on_command_end(self, cmd: Any, result: Any | None) -> None:
        self.calls.append(("command_end", type(cmd).__name__))

    async def on_command_error(self, cmd: Any, err: BaseException) -> None:
        self.calls.append(("command_error", type(cmd).__name__))

    async def on_event_start(self, evt: Any) -> None:
        self.calls.append(("event_start", type(evt).__name__))

    async def on_event_end(self, evt: Any) -> None:
        self.calls.append(("event_end", type(evt).__name__))

    async def on_event_error(self, evt: Any, err: BaseException) -> None:
        self.calls.append(("event_error", type(evt).__name__))

    async def on_uow_commit(self) -> None:
        self.calls.append(("uow_commit", None))

    async def on_uow_rollback(self) -> None:
        self.calls.append(("uow_rollback", None))


@pytest.fixture(name="FakeAsyncUnitOfWork")
def fixture_fake_async_unit_of_work():
    return FakeAsyncUnitOfWork


@pytest.fixture(name="RecordingHook")
def fixture_recording_hook():
    return RecordingHook


@pytest.fixture
def restored_user():
    def factory(
        *,
        email: str = "user@example.com",
        username: str = "user",
        password_hash: str = "hash",
        locale: str = "en",
    ) -> User:
        user = User.create(
            email=email,
            username=username,
            password_hash=password_hash,
            locale=locale,
        )
        tuple(user.pull_events())
        return user

    return factory
