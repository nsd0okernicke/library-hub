"""In-memory fake repositories for the Loan Service.

For tests and local development only – not for production use.
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
    """In-memory implementation of the LoanRepository port."""

    def __init__(self) -> None:
        self._store: Dict[uuid.UUID, Loan] = {}

    async def save(self, loan: Loan) -> None:
        """Store a loan in the in-memory store."""
        self._store[loan.id] = loan

    async def find_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        """Return a loan by ID or None if not found."""
        return self._store.get(loan_id)

    async def find_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Loan], int]:
        """Return all loans for a given user."""
        items = [l for l in self._store.values() if l.user_id == user_id]
        return items, len(items)

    async def find_overdue(self) -> Sequence[Loan]:
        """Return all overdue active loans."""
        from loan.domain.loan_status import LoanStatus
        today = date.today()
        return [
            l for l in self._store.values()
            if l.status == LoanStatus.ACTIVE and l.due_date < today
        ]


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of the UserRepository port."""

    def __init__(self) -> None:
        self._store: Dict[uuid.UUID, User] = {}
        self._emails: Dict[str, uuid.UUID] = {}

    async def save(self, user: User) -> None:
        """Store a user in the in-memory store."""
        self._store[user.id] = user
        self._emails[user.email] = user.id

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return a user by ID or None if not found."""
        return self._store.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        """Return a user by e-mail address or None if not found."""
        uid = self._emails.get(email)
        return self._store.get(uid) if uid else None

    async def exists_by_email(self, email: str) -> bool:
        """Return True if the e-mail address is already registered."""
        return email in self._emails


class InMemoryMessagePublisher(MessagePublisher):
    """In-memory fake implementation of the MessagePublisher port."""

    def __init__(self) -> None:
        self.published: list[dict] = []

    async def publish(self, routing_key: str, payload: dict) -> None:
        """Store routing key and payload in the in-memory list."""
        self.published.append({"routing_key": routing_key, "payload": payload})

