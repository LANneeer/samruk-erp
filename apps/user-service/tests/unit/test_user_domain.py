from __future__ import annotations
import pytest
from src.domains.users.model import Role, User
from src.dto.commands import (
    UserActivated,
    UserDeactivated,
    UserPasswordChanged,
    UserProfileUpdated,
    UserRegistered,
    UserRoleChanged,
)


def test_user_create_records_registration_event() -> None:
    user = User.create(
        email="ada@example.com",
        username="ada",
        password_hash="hash",
        locale="kk",
    )

    events = tuple(user.pull_events())

    assert user.email == "ada@example.com"
    assert user.username == "ada"
    assert user.role == Role.USER
    assert user.locale == "kk"
    assert len(events) == 1
    assert events[0] == UserRegistered(
        user_id=user.id,
        email="ada@example.com",
        username="ada",
        role="user",
        locale="kk",
    )
    assert tuple(user.pull_events()) == ()


def test_user_state_changes_record_domain_events(restored_user) -> None:
    user = restored_user(username="ada")

    user.rename("ada_admin")
    user.change_locale("ru")
    user.change_password_hash("new-hash")
    user.deactivate()
    user.activate()
    user.promote_to_admin()

    events = tuple(user.pull_events())

    assert user.username == "ada_admin"
    assert user.locale == "ru"
    assert user.is_active is True
    assert user.role == Role.ADMIN
    assert events == (
        UserProfileUpdated(user_id=user.id, changes={"username": "ada_admin"}),
        UserProfileUpdated(user_id=user.id, changes={"locale": "ru"}),
        UserPasswordChanged(user_id=user.id),
        UserDeactivated(user_id=user.id),
        UserActivated(user_id=user.id),
        UserRoleChanged(user_id=user.id, new_role="admin"),
    )


def test_user_ignores_noop_changes(restored_user) -> None:
    user = restored_user(username="ada", locale="en")

    user.rename("ada")
    user.change_locale("en")
    user.deactivate()
    user.deactivate()
    user.activate()
    user.activate()
    user.promote_to_admin()
    user.promote_to_admin()

    events = tuple(user.pull_events())

    assert events == (
        UserDeactivated(user_id=user.id),
        UserActivated(user_id=user.id),
        UserRoleChanged(user_id=user.id, new_role="admin"),
    )


def test_user_rejects_invalid_profile_and_password_values(restored_user) -> None:
    user = restored_user(username="ada")

    with pytest.raises(ValueError, match="Username"):
        user.rename("ad")

    with pytest.raises(ValueError, match="Locale"):
        user.change_locale("")

    with pytest.raises(ValueError, match="Password"):
        user.change_password_hash("")

    assert tuple(user.pull_events()) == ()
