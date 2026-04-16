"""Unit tests for GetUserByEmailUseCase (Loan Service).

Tested: loan.application.get_user_by_email_use_case.GetUserByEmailUseCase
"""

from __future__ import annotations

import uuid

import pytest

from loan.application.get_user_by_email_use_case import GetUserByEmailUseCase
from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User


class FakeUserRepository(UserRepository):
    """Minimal in-memory fake for use-case unit tests."""

    def __init__(self) -> None:
        self._store: dict[uuid.UUID, User] = {}
        self._emails: dict[str, uuid.UUID] = {}

    async def save(self, user: User) -> None:
        self._store[user.id] = user
        self._emails[user.email] = user.id

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._store.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        uid = self._emails.get(email)
        return self._store.get(uid) if uid else None

    async def exists_by_email(self, email: str) -> bool:
        return email in self._emails


class TestGetUserByEmailUseCase:
    """Unit tests for the e-mail login lookup use case."""

    @pytest.fixture
    def repo(self) -> FakeUserRepository:
        return FakeUserRepository()

    @pytest.fixture
    def use_case(self, repo: FakeUserRepository) -> GetUserByEmailUseCase:
        return GetUserByEmailUseCase(user_repo=repo)

    @pytest.mark.asyncio
    async def test_returns_user_when_email_exists(
        self, use_case: GetUserByEmailUseCase, repo: FakeUserRepository
    ) -> None:
        """Returns the correct User when the e-mail is registered."""
        existing = User(
            id=uuid.uuid4(), name="Alice", email="alice@example.com"
        )
        await repo.save(existing)

        result = await use_case.execute("alice@example.com")

        assert result.id == existing.id
        assert result.name == "Alice"
        assert result.email == "alice@example.com"

    @pytest.mark.asyncio
    async def test_raises_when_email_not_found(
        self, use_case: GetUserByEmailUseCase
    ) -> None:
        """Raises ValueError when no user with the given e-mail exists."""
        with pytest.raises(ValueError, match="alice@example.com"):
            await use_case.execute("alice@example.com")

    @pytest.mark.asyncio
    async def test_uses_repo_to_look_up_email(
        self, use_case: GetUserByEmailUseCase, repo: FakeUserRepository
    ) -> None:
        """Delegates the lookup to the repository (not a hardcoded result)."""
        user_a = User(id=uuid.uuid4(), name="Alice", email="alice@example.com")
        user_b = User(id=uuid.uuid4(), name="Bob", email="bob@example.com")
        await repo.save(user_a)
        await repo.save(user_b)

        result = await use_case.execute("bob@example.com")

        assert result.id == user_b.id
        assert result.name == "Bob"

    @pytest.mark.asyncio
    async def test_error_message_contains_email(
        self, use_case: GetUserByEmailUseCase
    ) -> None:
        """ValueError message includes the queried e-mail for debugging."""
        email = "unknown@example.com"
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(email)
        assert email in str(exc_info.value)

