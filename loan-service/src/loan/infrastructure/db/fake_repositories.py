"""In-Memory-Fake-Repositories für den Loan Service.

Nur für Tests und lokale Entwicklung – kein Produktionseinsatz.
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from typing import Dict

from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository
from loan.domain.ports.message_publisher import MessagePublisher
from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User


class InMemoryLoanRepository(LoanRepository):
    """In-Memory-Implementierung des LoanRepository-Ports."""

    def __init__(self) -> None:
        self._store: Dict[uuid.UUID, Loan] = {}

    async def save(self, loan: Loan) -> None:
        """Speichert eine Ausleihe im In-Memory-Store."""
        self._store[loan.id] = loan

    async def find_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        """Gibt eine Ausleihe per ID zurück oder None."""
        return self._store.get(loan_id)

    async def find_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Loan], int]:
        """Gibt alle Ausleihen eines Nutzers zurück."""
        items = [l for l in self._store.values() if l.user_id == user_id]
        return items, len(items)

    async def find_overdue(self) -> Sequence[Loan]:
        """Gibt alle überfälligen aktiven Ausleihen zurück."""
        from loan.domain.loan_status import LoanStatus
        today = date.today()
        return [
            l for l in self._store.values()
            if l.status == LoanStatus.ACTIVE and l.due_date < today
        ]


class InMemoryUserRepository(UserRepository):
    """In-Memory-Implementierung des UserRepository-Ports."""

    def __init__(self) -> None:
        self._store: Dict[uuid.UUID, User] = {}
        self._emails: Dict[str, uuid.UUID] = {}

    async def save(self, user: User) -> None:
        """Speichert einen Nutzer im In-Memory-Store."""
        self._store[user.id] = user
        self._emails[user.email] = user.id

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Gibt einen Nutzer per ID zurück oder None."""
        return self._store.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        """Gibt einen Nutzer per E-Mail zurück oder None."""
        uid = self._emails.get(email)
        return self._store.get(uid) if uid else None

    async def exists_by_email(self, email: str) -> bool:
        """Prüft ob eine E-Mail bereits registriert ist."""
        return email in self._emails


class InMemoryMessagePublisher(MessagePublisher):
    """In-Memory-Fake für den MessagePublisher-Port."""

    def __init__(self) -> None:
        self.published: list[dict] = []

    async def publish(self, routing_key: str, payload: dict) -> None:
        """Speichert Routing-Key und Payload im In-Memory-Store."""
        self.published.append({"routing_key": routing_key, "payload": payload})

