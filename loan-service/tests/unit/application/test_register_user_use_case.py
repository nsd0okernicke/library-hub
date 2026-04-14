"""Unit tests for RegisterUserUseCase (Loan Service).

🔴 RED phase: Tests must FAIL before any implementation exists.
Tested: loan.application.register_user_use_case.RegisterUserUseCase (LOAN-0)
"""

from __future__ import annotations

import uuid

import pytest

from loan.application.register_user_use_case import RegisterUserUseCase
from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User


class FakeUserRepository(UserRepository):
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


class TestRegisterUserUseCase:
    """LOAN-0: Register a new user."""

    @pytest.fixture
    def use_case(self) -> RegisterUserUseCase:
        return RegisterUserUseCase(user_repo=FakeUserRepository())

    @pytest.mark.asyncio
    async def test_register_new_user_returns_user(
        self, use_case: RegisterUserUseCase
    ) -> None:
        """New user is persisted and returned."""
        user = await use_case.execute(name="Alice Müller", email="alice@example.com")
        assert user.name == "Alice Müller"
        assert user.email == "alice@example.com"
        assert isinstance(user.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(
        self, use_case: RegisterUserUseCase
    ) -> None:
        """Duplicate e-mail raises ValueError (→ HTTP 409)."""
        await use_case.execute(name="Alice", email="alice@example.com")
        with pytest.raises(ValueError, match="[Aa]lready exists|[Dd]uplicate|email"):
            await use_case.execute(name="Alice 2", email="alice@example.com")

    @pytest.mark.asyncio
    async def test_register_persists_user(
        self, use_case: RegisterUserUseCase
    ) -> None:
        """Persisted user can be retrieved via the repository."""
        user = await use_case.execute(name="Bob", email="bob@example.com")
        found = await use_case._user_repo.find_by_id(user.id)
        assert found == user

