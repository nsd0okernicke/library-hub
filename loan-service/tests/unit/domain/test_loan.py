"""Unit-Tests für das Loan-Domain-Modell und LoanStatus (Loan Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klassen:
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
    """Tests für die LoanStatus-Enumeration."""

    def test_all_required_statuses_exist(self) -> None:
        """Alle vier Status-Werte müssen vorhanden sein."""
        assert LoanStatus.PENDING
        assert LoanStatus.ACTIVE
        assert LoanStatus.RETURNED
        assert LoanStatus.REJECTED

    def test_status_values_are_strings(self) -> None:
        """Status-Werte sind Strings (für Datenbankpersistierung)."""
        assert LoanStatus.PENDING.value == "PENDING"
        assert LoanStatus.ACTIVE.value == "ACTIVE"
        assert LoanStatus.RETURNED.value == "RETURNED"
        assert LoanStatus.REJECTED.value == "REJECTED"


class TestLoanCreation:
    """Tests für die Erzeugung eines Loan-Domänenobjekts."""

    def test_create_loan_with_all_fields(self) -> None:
        """Loan kann mit allen Pflichtfeldern erzeugt werden."""
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
        """Wird keine ID angegeben, wird automatisch eine UUID generiert."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        assert loan.id is not None
        assert isinstance(loan.id, uuid.UUID)

    def test_new_loan_status_is_pending(self) -> None:
        """Neu angelegte Ausleihe hat Status PENDING."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        assert loan.status == LoanStatus.PENDING

    def test_loan_returned_at_is_none_initially(self) -> None:
        """returned_at ist beim Anlegen None."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        assert loan.returned_at is None


class TestLoanStatusTransitions:
    """Tests für erlaubte und verbotene Zustandsübergänge (concept.md)."""

    def _make_loan(self) -> Loan:
        return Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )

    # ── Erlaubte Übergänge ──────────────────────────────────────────────────

    def test_pending_to_active_on_book_reserved(self) -> None:
        """PENDING → ACTIVE wenn BookReserved empfangen."""
        loan = self._make_loan()
        loan.activate()
        assert loan.status == LoanStatus.ACTIVE

    def test_pending_to_rejected_on_book_out_of_stock(self) -> None:
        """PENDING → REJECTED wenn BookOutOfStock empfangen."""
        loan = self._make_loan()
        loan.reject()
        assert loan.status == LoanStatus.REJECTED

    def test_active_to_returned(self) -> None:
        """ACTIVE → RETURNED bei Rückgabe."""
        loan = self._make_loan()
        loan.activate()
        loan.return_book()
        assert loan.status == LoanStatus.RETURNED

    def test_return_sets_returned_at(self) -> None:
        """return_book() setzt returned_at auf heute."""
        loan = self._make_loan()
        loan.activate()
        loan.return_book()
        assert loan.returned_at == date.today()

    # ── Verbotene Übergänge ─────────────────────────────────────────────────

    def test_returned_to_any_raises(self) -> None:
        """RETURNED → * ist verboten – Meldung beginnt mit 'Invalid' und enthält 'already returned'."""
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
        """REJECTED → * ist verboten – Meldung beginnt mit 'Invalid'."""
        loan = self._make_loan()
        loan.reject()
        with pytest.raises(ValueError) as exc_info:
            loan.activate()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert not msg.startswith("XX")

    def test_pending_to_returned_raises(self) -> None:
        """PENDING → RETURNED ist verboten – Meldung beginnt mit 'Invalid' und enthält 'not active'."""
        loan = self._make_loan()
        with pytest.raises(ValueError) as exc_info:
            loan.return_book()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert "not active" in msg
        assert not msg.startswith("XX")

    def test_active_to_rejected_raises(self) -> None:
        """ACTIVE → REJECTED ist verboten – Meldung beginnt mit 'Invalid'."""
        loan = self._make_loan()
        loan.activate()
        with pytest.raises(ValueError) as exc_info:
            loan.reject()
        msg = str(exc_info.value)
        assert msg.startswith("Invalid")
        assert not msg.startswith("XX")


class TestLoanOverdue:
    """Tests für die Überfälligkeits-Logik."""

    def test_loan_is_overdue_when_due_date_in_past(self) -> None:
        """ACTIVE Ausleihe mit due_date in der Vergangenheit ist überfällig."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        loan.activate()
        assert loan.is_overdue() is True

    def test_loan_is_not_overdue_when_due_date_in_future(self) -> None:
        """ACTIVE Ausleihe mit due_date in der Zukunft ist nicht überfällig."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=7),
        )
        loan.activate()
        assert loan.is_overdue() is False

    def test_loan_due_today_is_not_overdue(self) -> None:
        """ACTIVE Ausleihe mit due_date == heute ist NICHT überfällig (< today, nicht <=)."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today(),
        )
        loan.activate()
        assert loan.is_overdue() is False

    def test_pending_loan_is_never_overdue(self) -> None:
        """PENDING Ausleihe ist nie überfällig, auch wenn due_date vergangen."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        assert loan.is_overdue() is False

    def test_rejected_loan_is_never_overdue(self) -> None:
        """REJECTED Ausleihe ist nie überfällig."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        loan.reject()
        assert loan.is_overdue() is False

    def test_returned_loan_is_not_overdue(self) -> None:
        """Zurückgegebene Ausleihe gilt nicht als überfällig."""
        loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        loan.activate()
        loan.return_book()
        assert loan.is_overdue() is False

