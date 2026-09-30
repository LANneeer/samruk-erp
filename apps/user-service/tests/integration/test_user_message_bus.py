from __future__ import annotations
import asyncio
import pytest
from src.bootstrap.async_settings import bootstrap_async
from utils.domains.common.exceptions import Conflict, DuplicateEmail
from src.dto.commands import RegisterUser, UpdateUserProfile


class SpyNotifier:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, *, channel: str, message: str) -> None:
        self.sent.append({"channel": channel, "message": message})


class SpyPublisher:
    def __init__(self) -> None:
        self.published: list[dict[str, object]] = []

    async def publish(self, topic: str, payload: dict[str, object]) -> None:
        self.published.append({"topic": topic, "payload": payload})


def test_register_user_flows_through_command_uow_event_and_observability(
    FakeAsyncUnitOfWork,
    RecordingHook,
) -> None:
    async def scenario() -> None:
        uow = FakeAsyncUnitOfWork()
        hook = RecordingHook()
        uow.set_observability_hook(hook)
        notifier = SpyNotifier()
        publisher = SpyPublisher()
        bus = bootstrap_async(
            uow,
            hook=hook,
            notifier=notifier,
            publisher=publisher,
        )

        results = await bus.handle(
            RegisterUser(
                email="ada@example.com",
                username="ada",
                password_hash="hash",
                locale="kk",
            )
        )

        user_id = results[0]
        user = await uow.users.get_async(user_id)
        assert user is not None
        assert user.email == "ada@example.com"
        assert user.username == "ada"
        assert user.locale == "kk"
        assert uow.commits == 1
        assert notifier.sent == [
            {
                "channel": "telegram",
                "message": "New user registered: ada (ada@example.com)",
            }
        ]
        assert publisher.published == [
            {
                "topic": "user.registered",
                "payload": {"user_id": str(user_id), "email": "ada@example.com"},
            }
        ]
        assert hook.calls == [
            ("command_start", "RegisterUser"),
            ("uow_commit", None),
            ("command_end", "RegisterUser"),
            ("event_start", "UserRegistered"),
            ("event_end", "UserRegistered"),
        ]

    asyncio.run(scenario())


def test_register_user_rejects_duplicate_email(
    FakeAsyncUnitOfWork,
    restored_user,
) -> None:
    async def scenario() -> None:
        uow = FakeAsyncUnitOfWork()
        uow.users.add(restored_user(email="ada@example.com", username="ada"))
        bus = bootstrap_async(uow)

        with pytest.raises(DuplicateEmail):
            await bus.handle(
                RegisterUser(
                    email="ada@example.com",
                    username="other",
                    password_hash="hash",
                )
            )

        assert uow.commits == 0

    asyncio.run(scenario())


def test_update_profile_rejects_duplicate_username_without_commit(
    FakeAsyncUnitOfWork,
    restored_user,
) -> None:
    async def scenario() -> None:
        target = restored_user(email="ada@example.com", username="ada")
        existing = restored_user(email="grace@example.com", username="grace")
        uow = FakeAsyncUnitOfWork()
        uow.users.add(target)
        uow.users.add(existing)
        bus = bootstrap_async(uow)

        with pytest.raises(Conflict):
            await bus.handle(
                UpdateUserProfile(
                    user_id=target.id,
                    new_username="grace",
                    new_locale="kk",
                )
            )

        assert target.username == "ada"
        assert target.locale == "en"
        assert uow.commits == 0

    asyncio.run(scenario())
