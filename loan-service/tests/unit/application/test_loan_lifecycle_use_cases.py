"""Unit tests for loan lifecycle use cases (Loan Service).

Tested:
  loan.application.activate_loan_use_case.ActivateLoanUseCase   (PENDING→ACTIVE)
  loan.application.reject_loan_use_case.RejectLoanUseCase        (PENDING→REJECTED)
  loan.application.return_loan_use_case.ReturnLoanUseCase        (ACTIVE→RETURNED, LOAN-4)
  loan.application.get_loan_use_case.GetLoanUseCase              (LOAN-2)
  loan.application.list_loans_use_case.ListLoansUseCase          (LOAN-3)
  loan.application.list_overdue_loans_use_case.ListOverdueLoansUseCase (LOAN-5)
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

import pytest

from loan.application.activate_loan_use_case import ActivateLoanUseCase
from loan.application.get_loan_use_case import GetLoanUseCase
from loan.application.list_loans_use_case import ListLoansUseCase
from loan.application.list_overdue_loans_use_case import ListOverdueLoansUseCase
from loan.application.reject_loan_use_case import RejectLoanUseCase
from loan.application.return_loan_use_case import ReturnLoanUseCase
from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.loan_status import LoanStatus
from loan.domain.ports.loan_repository import LoanRepository
from loan.domain.ports.message_publisher import MessagePublisher

_ISBN = Isbn("978-3-16-148410-0")
_USER_ID = uuid.uuid4()


# ── Fakes ─────────────────────────────────────────────────────────────────────

class FakeLoanRepository(LoanRepository):
    def __init__(self, loans: list[Loan] | None = None) -> None:
        self._store: dict[uuid.UUID, Loan] = {
            loan.id: loan for loan in (loans or [])
        }

    async def save(self, loan: Loan) -> None:
        self._store[loan.id] = loan

    async def find_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return self._store.get(loan_id)

    async def find_by_user_id(
        self, user_id: uuid.UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[Loan], int]:
        results = [loan for loan in self._store.values() if loan.user_id == user_id]
        total = len(results)
        start = (page - 1) * page_size
        return results[start : start + page_size], total

    async def find_overdue(self) -> Sequence[Loan]:
        return [loan for loan in self._store.values() if loan.is_overdue()]


class FakeMessagePublisher(MessagePublisher):
    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        self.published.append({"routing_key": routing_key, "payload": payload})


def _pending_loan() -> Loan:
    return Loan(
        user_id=_USER_ID,
        isbn=_ISBN,
        due_date=date.today() + timedelta(days=28),
    )


def _active_loan() -> Loan:
    loan = _pending_loan()
    loan.activate()
    return loan


def _overdue_loan() -> Loan:
    loan = Loan(
        user_id=_USER_ID,
        isbn=_ISBN,
        due_date=date.today() - timedelta(days=1),
    )
    loan.activate()
    return loan


# ── ActivateLoanUseCase ───────────────────────────────────────────────────────

class TestActivateLoanUseCase:
    """PENDING → ACTIVE after BookReserved event."""

    @pytest.mark.asyncio
    async def test_activate_pending_loan(self) -> None:
        """Loan transitions from PENDING to ACTIVE."""
        loan = _pending_loan()
        repo = FakeLoanRepository(loans=[loan])
        use_case = ActivateLoanUseCase(loan_repo=repo)
        activated = await use_case.execute(loan_id=loan.id)
        assert activated.status == LoanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_unknown_loan_raises(self) -> None:
        """Unknown loan_id raises ValueError."""
        use_case = ActivateLoanUseCase(loan_repo=FakeLoanRepository())
        with pytest.raises(ValueError, match="[Nn]ot found"):
            await use_case.execute(loan_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_activate_non_pending_loan_raises(self) -> None:
        """An already active loan cannot be activated again."""
        loan = _active_loan()
        use_case = ActivateLoanUseCase(loan_repo=FakeLoanRepository(loans=[loan]))
        with pytest.raises(ValueError):
            await use_case.execute(loan_id=loan.id)


# ── RejectLoanUseCase ─────────────────────────────────────────────────────────

class TestRejectLoanUseCase:
    """PENDING → REJECTED after BookOutOfStock event."""

    @pytest.mark.asyncio
    async def test_reject_pending_loan(self) -> None:
        """Loan transitions from PENDING to REJECTED."""
        loan = _pending_loan()
        use_case = RejectLoanUseCase(loan_repo=FakeLoanRepository(loans=[loan]))
        rejected = await use_case.execute(loan_id=loan.id)
        assert rejected.status == LoanStatus.REJECTED

    @pytest.mark.asyncio
    async def test_reject_unknown_loan_raises(self) -> None:
        """Unknown loan_id raises ValueError."""
        use_case = RejectLoanUseCase(loan_repo=FakeLoanRepository())
        with pytest.raises(ValueError, match="[Nn]ot found"):
            await use_case.execute(loan_id=uuid.uuid4())


# ── ReturnLoanUseCase ─────────────────────────────────────────────────────────

class TestReturnLoanUseCase:
    """LOAN-4: Return a book – ACTIVE → RETURNED + publish BookReturned."""

    def _make_use_case(
        self, loan: Loan
    ) -> tuple[ReturnLoanUseCase, FakeMessagePublisher]:
        publisher = FakeMessagePublisher()
        use_case = ReturnLoanUseCase(
            loan_repo=FakeLoanRepository(loans=[loan]),
            publisher=publisher,
        )
        return use_case, publisher

    @pytest.mark.asyncio
    async def test_return_active_loan(self) -> None:
        """ACTIVE → RETURNED."""
        loan = _active_loan()
        use_case, _ = self._make_use_case(loan)
        returned = await use_case.execute(loan_id=loan.id)
        assert returned.status == LoanStatus.RETURNED

    @pytest.mark.asyncio
    async def test_return_publishes_book_returned_event(self) -> None:
        """BookReturned event is published (requirements.md §8)."""
        loan = _active_loan()
        use_case, publisher = self._make_use_case(loan)
        await use_case.execute(loan_id=loan.id)
        assert len(publisher.published) == 1
        msg = publisher.published[0]
        assert msg["routing_key"] == "book.returned"
        payload = msg["payload"]
        assert payload["event_type"] == "BookReturned"
        assert payload["version"] == "1.0"
        assert payload["loan_id"] == str(loan.id)
        assert payload["isbn"] == str(_ISBN)

    @pytest.mark.asyncio
    async def test_return_already_returned_raises(self) -> None:
        """Returning an already returned loan raises ValueError (→ HTTP 409)."""
        loan = _active_loan()
        use_case, _ = self._make_use_case(loan)
        await use_case.execute(loan_id=loan.id)
        with pytest.raises(ValueError):
            await use_case.execute(loan_id=loan.id)

    @pytest.mark.asyncio
    async def test_return_unknown_loan_raises(self) -> None:
        """Unknown loan_id raises ValueError (→ HTTP 404)."""
        publisher = FakeMessagePublisher()
        use_case = ReturnLoanUseCase(
            loan_repo=FakeLoanRepository(),
            publisher=publisher,
        )
        with pytest.raises(ValueError, match="[Nn]ot found"):
            await use_case.execute(loan_id=uuid.uuid4())


# ── GetLoanUseCase ────────────────────────────────────────────────────────────

class TestGetLoanUseCase:
    """LOAN-2: Retrieve a single loan."""

    @pytest.mark.asyncio
    async def test_get_existing_loan(self) -> None:
        """Known loan_id returns the loan."""
        loan = _pending_loan()
        use_case = GetLoanUseCase(loan_repo=FakeLoanRepository(loans=[loan]))
        result = await use_case.execute(loan_id=loan.id)
        assert result == loan

    @pytest.mark.asyncio
    async def test_get_unknown_loan_raises(self) -> None:
        """Unknown loan_id raises ValueError (→ HTTP 404)."""
        use_case = GetLoanUseCase(loan_repo=FakeLoanRepository())
        with pytest.raises(ValueError, match="[Nn]ot found"):
            await use_case.execute(loan_id=uuid.uuid4())


# ── ListLoansUseCase ──────────────────────────────────────────────────────────

class TestListLoansUseCase:
    """LOAN-3: List all loans for a user."""

    @pytest.mark.asyncio
    async def test_list_loans_for_user(self) -> None:
        """Returns all loans belonging to the given user."""
        loan1 = _pending_loan()
        loan2 = _active_loan()
        other = Loan(
            user_id=uuid.uuid4(), isbn=_ISBN,
            due_date=date.today() + timedelta(days=28)
        )
        use_case = ListLoansUseCase(
            loan_repo=FakeLoanRepository(loans=[loan1, loan2, other])
        )
        loans, total = await use_case.execute(user_id=_USER_ID)
        assert total == 2

    @pytest.mark.asyncio
    async def test_list_loans_empty(self) -> None:
        """No loans → empty list, no error raised."""
        use_case = ListLoansUseCase(loan_repo=FakeLoanRepository())
        loans, total = await use_case.execute(user_id=uuid.uuid4())
        assert total == 0
        assert list(loans) == []

    @pytest.mark.asyncio
    async def test_list_loans_pagination(self) -> None:
        """Pagination works correctly."""
        loans = [_pending_loan(), _pending_loan(), _pending_loan()]
        use_case = ListLoansUseCase(loan_repo=FakeLoanRepository(loans=loans))
        result, total = await use_case.execute(user_id=_USER_ID, page=1, page_size=2)
        assert total == 3
        assert len(list(result)) == 2


# ── ListOverdueLoansUseCase ───────────────────────────────────────────────────

class TestListOverdueLoansUseCase:
    """LOAN-5: List overdue loans."""

    @pytest.mark.asyncio
    async def test_list_overdue_returns_only_overdue(self) -> None:
        """Only ACTIVE loans with due_date < today are returned."""
        overdue = _overdue_loan()
        active = _active_loan()
        pending = _pending_loan()
        use_case = ListOverdueLoansUseCase(
            loan_repo=FakeLoanRepository(loans=[overdue, active, pending])
        )
        result = await use_case.execute()
        loans_list = list(result)
        assert len(loans_list) == 1
        assert loans_list[0].id == overdue.id

    @pytest.mark.asyncio
    async def test_list_overdue_empty(self) -> None:
        """No overdue loans → empty list."""
        use_case = ListOverdueLoansUseCase(loan_repo=FakeLoanRepository())
        result = await use_case.execute()
        assert list(result) == []

