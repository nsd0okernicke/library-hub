"""Unit tests for the Loan domain model and LoanStatus (Loan Service).

🔴 RED phase: These tests must FAIL before any implementation exists.
Tested classes:
    - loan.domain.loan_status.LoanStatus
    - loan.domain.loan.Loan
"""

import uuid
from datetime import date, timedelta

import pytest

from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.loan_status import LoanStatus

_ISBN = Isbn("978-3-16-148410-0")


class TestLoanStatus:
    """Tests for the LoanStatus enumeration."""

    def test_all_required_statuses_exist(self) -> None:
        """All four status values must be present."""
        assert LoanStatus.PENDING
        assert LoanStatus.ACTIVE
        assert LoanStatus.RETURNED
        assert LoanStatus.REJECTED

    def test_status_values_are_strings(self) -> None:
        """Status values are strings (required for database persistence)."""
        assert LoanStatus.PENDING.value == "PENDING"
        assert LoanStatus.ACTIVE.value == "ACTIVE"
        assert LoanStatus.RETURNED.value == "RETURNED"
        assert LoanStatus.REJECTED.value == "REJECTED"


class TestLoanCreation:
    """Tests for creating a Loan domain object."""

    def test_create_loan_with_all_fields(self) -> None:
        """Loan can be created with all required fields."""
        loan_id = uuid.uuid4()
        user_id = uuid.uuid4()
        due = date.today() + timedelta(days=28)
        loan = Loan(
            id=loan_id,
            user_id=user_id,
            isbn=_ISBN,
            due_date=due,
        )
        assert loan.id == loan_id
        assert loan.user_id == user_id
        assert loan.isbn == _ISBN
        assert loan.due_date == due
        assert loan.status == LoanStatus.PENDING

    def test_create_loan_without_id_generates_uuid(self) -> None:
        """When no id is given, a UUID is generated automatically."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        assert loan.id is not None
        assert isinstance(loan.id, uuid.UUID)

    def test_new_loan_status_is_pending(self) -> None:
        """A newly created loan has status PENDING."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        assert loan.status == LoanStatus.PENDING

    def test_loan_returned_at_is_none_initially(self) -> None:
        """returned_at is None when the loan is first created."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        assert loan.returned_at is None


class TestLoanStatusTransitions:
    """Tests for allowed and forbidden status transitions (see concept.md)."""

    def _make_loan(self) -> Loan:
        return Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )

    # ── Allowed transitions ──────────────────────────────────────────────────

    def test_pending_to_active_on_book_reserved(self) -> None:
        """PENDING → ACTIVE when BookReserved is received."""
        loan = self._make_loan()
        loan.activate()
        assert loan.status == LoanStatus.ACTIVE

    def test_pending_to_rejected_on_book_out_of_stock(self) -> None:
        """PENDING → REJECTED when BookOutOfStock is received."""
        loan = self._make_loan()
        loan.reject()
        assert loan.status == LoanStatus.REJECTED

    def test_active_to_returned(self) -> None:
        """ACTIVE → RETURNED when the book is returned."""
        loan = self._make_loan()
        loan.activate()
        loan.return_book()
        assert loan.status == LoanStatus.RETURNED

    def test_return_sets_returned_at(self) -> None:
        """return_book() sets returned_at to today."""
        loan = self._make_loan()
        loan.activate()
        loan.return_book()
        assert loan.returned_at == date.today()

    # ── Forbidden transitions ─────────────────────────────────────────────────

    def test_returned_to_any_raises(self) -> None:
        """RETURNED → * is forbidden – message starts with 'Invalid' and contains 'already returned'."""
        loan = self._make_loan()
        loan.activate()
        loan.return_book()
        with pytest.raises(ValueError) as exc_info:
            loan.return_book()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert "already returned" in msg
        assert not msg.startswith("XX")

    def test_rejected_to_any_raises(self) -> None:
        """REJECTED → * is forbidden – message starts with 'Invalid'."""
        loan = self._make_loan()
        loan.reject()
        with pytest.raises(ValueError) as exc_info:
            loan.activate()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert not msg.startswith("XX")

    def test_pending_to_returned_raises(self) -> None:
        """PENDING → RETURNED is forbidden – message starts with 'Invalid' and contains 'not active'."""
        loan = self._make_loan()
        with pytest.raises(ValueError) as exc_info:
            loan.return_book()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert "not active" in msg
        # kill mutant: error text must NOT be wrapped in XX...XX
        assert "XX" not in msg
        assert not msg.startswith("XX")

    def test_active_to_rejected_raises(self) -> None:
        """ACTIVE → REJECTED is forbidden – message starts with 'Invalid'."""
        loan = self._make_loan()
        loan.activate()
        with pytest.raises(ValueError) as exc_info:
            loan.reject()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert not msg.startswith("XX")


class TestLoanOverdue:
    """Tests for the overdue logic."""

    def test_loan_is_overdue_when_due_date_in_past(self) -> None:
        """ACTIVE loan with due_date in the past is overdue."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        loan.activate()
        assert loan.is_overdue() is True

    def test_loan_is_not_overdue_when_due_date_in_future(self) -> None:
        """ACTIVE loan with due_date in the future is not overdue."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=7),
        )
        loan.activate()
        assert loan.is_overdue() is False

    def test_loan_due_today_is_not_overdue(self) -> None:
        """ACTIVE loan with due_date == today is NOT overdue (uses < not <=)."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today(),
        )
        loan.activate()
        assert loan.is_overdue() is False

    def test_pending_loan_is_never_overdue(self) -> None:
        """PENDING loan is never overdue, even if due_date has passed."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        assert loan.is_overdue() is False

    def test_rejected_loan_is_never_overdue(self) -> None:
        """REJECTED loan is never overdue."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        loan.reject()
        assert loan.is_overdue() is False

    def test_returned_loan_is_not_overdue(self) -> None:
        """A returned loan is not considered overdue."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        loan.activate()
        loan.return_book()
        assert loan.is_overdue() is False

