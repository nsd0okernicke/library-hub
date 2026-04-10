"""Contract-Tests für den UserRepository-Port (Loan Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: loan.ports.user_repository.UserRepository
"""

from __future__ import annotations

import uuid

import pytest

from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User

_USER = User(name="Alice Müller", email="alice@example.com")


class FakeUserRepository(UserRepository):
    """In-Memory-Implementierung des UserRepository-Ports für Tests."""

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
        if uid is None:
            return None
        return self._store.get(uid)

    async def exists_by_email(self, email: str) -> bool:
        return email in self._emails


class TestUserRepositoryIsAbstract:
    """Der Port muss ein abstraktes Interface sein."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """UserRepository kann nicht direkt instanziiert werden."""
        with pytest.raises(TypeError):
            UserRepository()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        """Eine konkrete Implementierung kann instanziiert werden."""
        repo = FakeUserRepository()
        assert repo is not None


class TestUserRepositoryContract:
    """Vertrag: FakeUserRepository muss alle Port-Methoden korrekt implementieren."""

    @pytest.fixture
    def repo(self) -> FakeUserRepository:
        return FakeUserRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo: FakeUserRepository) -> None:
        """save() + find_by_id() – User speichern und abrufen."""
        await repo.save(_USER)
        result = await repo.find_by_id(_USER.id)
        assert result == _USER

    @pytest.mark.asyncio
    async def test_find_by_id_unknown_returns_none(
        self, repo: FakeUserRepository
    ) -> None:
        """find_by_id() gibt None zurück für unbekannte ID."""
        result = await repo.find_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_email(self, repo: FakeUserRepository) -> None:
        """find_by_email() gibt User zurück wenn E-Mail bekannt ist."""
        await repo.save(_USER)
        result = await repo.find_by_email("alice@example.com")
        assert result == _USER

    @pytest.mark.asyncio
    async def test_find_by_email_unknown_returns_none(
        self, repo: FakeUserRepository
    ) -> None:
        """find_by_email() gibt None zurück wenn E-Mail unbekannt ist."""
        result = await repo.find_by_email("unknown@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_by_email_true(self, repo: FakeUserRepository) -> None:
        """exists_by_email() gibt True wenn E-Mail registriert ist."""
        await repo.save(_USER)
        assert await repo.exists_by_email("alice@example.com") is True

    @pytest.mark.asyncio
    async def test_exists_by_email_false(self, repo: FakeUserRepository) -> None:
        """exists_by_email() gibt False wenn E-Mail nicht registriert ist."""
        assert await repo.exists_by_email("unknown@example.com") is False

