"""Unit tests for the User domain model (Loan Service).

Tested class: loan.domain.user.User
"""

import uuid

import pytest

from loan.domain.user import User


class TestUserCreation:
    """Tests for creating a User domain object."""

    def test_create_user_with_all_fields(self) -> None:
        """User can be created with all fields provided."""
        user_id = uuid.uuid4()
        user = User(id=user_id, name="Alice Müller", email="alice@example.com")
        assert user.id == user_id
        assert user.name == "Alice Müller"
        assert user.email == "alice@example.com"

    def test_create_user_without_id_generates_uuid(self) -> None:
        """When no id is given, a UUID is generated automatically."""
        user = User(name="Bob Schmidt", email="bob@example.com")
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)

    def test_two_users_with_same_id_are_equal(self) -> None:
        """Two users with the same id are considered equal."""
        uid = uuid.uuid4()
        user_a = User(id=uid, name="Alice", email="alice@example.com")
        user_b = User(id=uid, name="Different Name", email="other@example.com")
        assert user_a == user_b

    def test_two_users_with_different_id_are_not_equal(self) -> None:
        """Two users with different ids are not equal."""
        user_a = User(name="Alice", email="alice@example.com")
        user_b = User(name="Alice", email="alice@example.com")
        assert user_a != user_b

    def test_user_email_must_not_be_empty(self) -> None:
        """Empty email raises ValueError – message starts with 'User email'."""
        with pytest.raises(ValueError) as exc_info:
            User(name="Alice", email="")
        msg = str(exc_info.value)
        assert msg.startswith("User email")
        assert "not be empty" in msg
        assert not msg.startswith("XX")

    def test_user_name_must_not_be_empty(self) -> None:
        """Empty name raises ValueError – message starts with 'User name'."""
        with pytest.raises(ValueError) as exc_info:
            User(name="", email="alice@example.com")
        msg = str(exc_info.value)
        assert msg.startswith("User name")
        assert "not be empty" in msg
        assert not msg.startswith("XX")

    def test_user_not_equal_to_non_user(self) -> None:
        """Comparing a User with a non-User returns NotImplemented."""
        user = User(name="Alice", email="alice@example.com")
        assert user.__eq__("not-a-user") is NotImplemented

    def test_user_hashable_and_usable_in_set(self) -> None:
        """User is hashable and can be stored in a set."""
        import uuid as _uuid
        uid = _uuid.uuid4()
        user_a = User(id=uid, name="Alice", email="alice@example.com")
        user_b = User(id=uid, name="Alice Copy", email="copy@example.com")
        user_c = User(name="Bob", email="bob@example.com")
        user_set = {user_a, user_b, user_c}
        assert len(user_set) == 2

    def test_user_repr_contains_id_and_email(self) -> None:
        """__repr__ starts with 'User(' and contains email (no 'XX' prefix)."""
        user = User(name="Alice", email="alice@example.com")
        r = repr(user)
        assert r.startswith("User(")
        assert "alice@example.com" in r
        assert not r.startswith("XX")
