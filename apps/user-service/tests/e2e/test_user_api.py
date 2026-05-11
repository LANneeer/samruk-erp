from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.cli import fastapi_app
from src.infrastructure import middleware as middleware_module


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    async def get(self, key: str) -> bytes | None:
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: bytes) -> bool:
        self.store[key] = value
        return True


@pytest.fixture
def api_client(monkeypatch, FakeAsyncUnitOfWork):
    uow = FakeAsyncUnitOfWork()
    redis = FakeRedis()

    class FakeRedisFactory:
        @classmethod
        async def from_url(cls, *args, **kwargs) -> FakeRedis:
            return redis

    async def override_get_uow():
        yield uow

    monkeypatch.setattr(middleware_module, "Redis", FakeRedisFactory)
    fastapi_app.app.dependency_overrides[fastapi_app.get_uow] = override_get_uow
    fastapi_app.app.middleware_stack = None

    try:
        with TestClient(fastapi_app.app) as client:
            yield client, uow, redis
    finally:
        fastapi_app.app.dependency_overrides.clear()
        fastapi_app.app.middleware_stack = None


def test_user_api_lifecycle(api_client) -> None:
    client, uow, redis = api_client

    created = client.post(
        "/users",
        json={
            "email": "ada@example.com",
            "username": "ada",
            "password": "secret",
            "locale": "kk",
        },
    )
    assert created.status_code == 201
    body = created.json()
    user_id = body["id"]
    assert body == {
        "id": user_id,
        "email": "ada@example.com",
        "username": "ada",
        "role": "user",
        "locale": "kk",
        "is_active": True,
    }

    listed = client.get("/users", headers={"Idempotency-Key": "list"})
    assert listed.status_code == 200
    assert listed.json() == [body]

    profile = client.get(
        f"/users/{user_id}", headers={"Idempotency-Key": "profile-before"}
    )
    assert profile.status_code == 200
    assert profile.json() == body

    updated = client.patch(
        f"/users/{user_id}",
        json={"username": "ada_admin", "locale": "ru"},
    )
    assert updated.status_code == 200
    assert updated.json()["username"] == "ada_admin"
    assert updated.json()["locale"] == "ru"

    deactivated = client.post(f"/users/{user_id}/deactivate")
    assert deactivated.status_code == 204

    promoted = client.post(f"/users/{user_id}/promote")
    assert promoted.status_code == 204

    profile_after = client.get(
        f"/users/{user_id}", headers={"Idempotency-Key": "profile-after"}
    )
    assert profile_after.status_code == 200
    assert profile_after.json() == {
        "id": user_id,
        "email": "ada@example.com",
        "username": "ada_admin",
        "role": "admin",
        "locale": "ru",
        "is_active": False,
    }
    assert uow.commits == 4
    assert redis.store


def test_user_api_duplicate_email_returns_conflict(api_client) -> None:
    client, _, _ = api_client

    created = client.post(
        "/users",
        json={
            "email": "ada@example.com",
            "username": "ada",
            "password": "secret",
        },
    )
    assert created.status_code == 201

    duplicated = client.post(
        "/users",
        json={
            "email": "ada@example.com",
            "username": "grace",
            "password": "secret",
        },
    )

    assert duplicated.status_code == 409
    assert duplicated.json()["error"]["type"] == "DuplicateEmail"
