"""Unit tests for RequestLoanUseCase (Loan Service).

🔴 RED phase: Tests must FAIL before any implementation exists.
Tested: loan.application.request_loan_use_case.RequestLoanUseCase (LOAN-1)

Flow: POST /loans → create Loan(PENDING) → publish BookLoanRequested.
due_date = today + LOAN_DURATION_DAYS (configurable, default 28).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

import pytest

from loan.application.request_loan_use_case import RequestLoanUseCase
from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.loan_status import LoanStatus
from loan.domain.ports.loan_repository import LoanRepository
from loan.domain.ports.message_publisher import MessagePublisher

_ISBN = Isbn("978-3-16-148410-0")
_USER_ID = uuid.uuid4()


class FakeLoanRepository(LoanRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Loan] = {}

    async def save(self, loan: Loan) -> None:
        self._store[loan.id] = loan

    async def find_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return self._store.get(loan_id)

    async def find_by_user_id(
        self, user_id: uuid.UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[Loan], int]:
        results = [
            loan for loan in self._store.values() if loan.user_id == user_id
        ]
        return results, len(results)

    async def find_overdue(self) -> Sequence[Loan]:
        return [
            loan for loan in self._store.values() if loan.is_overdue()
        ]


class FakeMessagePublisher(MessagePublisher):
    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        self.published.append({"routing_key": routing_key, "payload": payload})


class TestRequestLoanUseCase:
    """LOAN-1: Request a book loan."""

    @pytest.fixture
    def publisher(self) -> FakeMessagePublisher:
        return FakeMessagePublisher()

    @pytest.fixture
    def use_case(self, publisher: FakeMessagePublisher) -> RequestLoanUseCase:
        return RequestLoanUseCase(
            loan_repo=FakeLoanRepository(),
            publisher=publisher,
            loan_duration_days=28,
        )

    @pytest.mark.asyncio
    async def test_request_loan_returns_pending_loan(
        self, use_case: RequestLoanUseCase
    ) -> None:
        """New loan has status PENDING."""
        loan = await use_case.execute(isbn=_ISBN, user_id=_USER_ID)
        assert loan.status == LoanStatus.PENDING
        assert loan.isbn == _ISBN
        assert loan.user_id == _USER_ID

    @pytest.mark.asyncio
    async def test_request_loan_sets_due_date(
        self, use_case: RequestLoanUseCase
    ) -> None:
        """due_date = today + 28 days."""
        loan = await use_case.execute(isbn=_ISBN, user_id=_USER_ID)
        assert loan.due_date == date.today() + timedelta(days=28)

    @pytest.mark.asyncio
    async def test_request_loan_respects_custom_duration(
        self, publisher: FakeMessagePublisher
    ) -> None:
        """loan_duration_days is configurable."""
        use_case = RequestLoanUseCase(
            loan_repo=FakeLoanRepository(),
            publisher=publisher,
            loan_duration_days=14,
        )
        loan = await use_case.execute(isbn=_ISBN, user_id=_USER_ID)
        assert loan.due_date == date.today() + timedelta(days=14)

    @pytest.mark.asyncio
    async def test_request_loan_publishes_book_loan_requested(
        self, use_case: RequestLoanUseCase, publisher: FakeMessagePublisher
    ) -> None:
        """BookLoanRequested event is published (requirements.md §8)."""
        loan = await use_case.execute(isbn=_ISBN, user_id=_USER_ID)
        assert len(publisher.published) == 1
        msg = publisher.published[0]
        assert msg["routing_key"] == "book.loan.requested"
        payload = msg["payload"]
        assert payload["event_type"] == "BookLoanRequested"
        assert payload["version"] == "1.0"
        assert payload["loan_id"] == str(loan.id)
        assert payload["isbn"] == str(_ISBN)
        assert payload["user_id"] == str(_USER_ID)

    @pytest.mark.asyncio
    async def test_request_loan_persists_loan(
        self, use_case: RequestLoanUseCase
    ) -> None:
        """Loan is persisted in the repository."""
        loan = await use_case.execute(isbn=_ISBN, user_id=_USER_ID)
        found = await use_case._loan_repo.find_by_id(loan.id)
        assert found == loan

