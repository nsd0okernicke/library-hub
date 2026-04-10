"""Contract-Tests für den LoanRepository-Port (Loan Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: loan.ports.loan_repository.LoanRepository
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, timedelta

import pytest

from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.loan_status import LoanStatus
from loan.domain.ports.loan_repository import LoanRepository

_ISBN = Isbn("978-3-16-148410-0")
_USER_ID = uuid.uuid4()


def _make_loan(status: LoanStatus = LoanStatus.PENDING) -> Loan:
    loan = Loan(
        user_id=_USER_ID,
        isbn=_ISBN,
        due_date=date.today() + timedelta(days=28),
    )
    if status == LoanStatus.ACTIVE:
        loan.activate()
    elif status == LoanStatus.REJECTED:
        loan.reject()
    elif status == LoanStatus.RETURNED:
        loan.activate()
        loan.return_book()
    return loan


class FakeLoanRepository(LoanRepository):
    """In-Memory-Implementierung des LoanRepository-Ports für Tests."""

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
        total = len(results)
        start = (page - 1) * page_size
        return results[start : start + page_size], total

    async def find_overdue(self) -> Sequence[Loan]:
        return [
            loan for loan in self._store.values() if loan.is_overdue()
        ]


class TestLoanRepositoryIsAbstract:
    """Der Port muss ein abstraktes Interface sein."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """LoanRepository kann nicht direkt instanziiert werden."""
        with pytest.raises(TypeError):
            LoanRepository()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        """Eine konkrete Implementierung kann instanziiert werden."""
        repo = FakeLoanRepository()
        assert repo is not None


class TestLoanRepositoryContract:
    """Vertrag: FakeLoanRepository muss alle Port-Methoden korrekt implementieren."""

    @pytest.fixture
    def repo(self) -> FakeLoanRepository:
        return FakeLoanRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo: FakeLoanRepository) -> None:
        """save() + find_by_id() – Loan speichern und abrufen."""
        loan = _make_loan()
        await repo.save(loan)
        result = await repo.find_by_id(loan.id)
        assert result == loan

    @pytest.mark.asyncio
    async def test_find_by_id_unknown_returns_none(
        self, repo: FakeLoanRepository
    ) -> None:
        """find_by_id() gibt None zurück für unbekannte ID."""
        result = await repo.find_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_user_id(self, repo: FakeLoanRepository) -> None:
        """find_by_user_id() gibt alle Loans eines Nutzers zurück."""
        loan1 = _make_loan()
        loan2 = _make_loan()
        other_loan = Loan(
            user_id=uuid.uuid4(),
            isbn=_ISBN,
            due_date=date.today() + timedelta(days=28),
        )
        await repo.save(loan1)
        await repo.save(loan2)
        await repo.save(other_loan)
        loans, total = await repo.find_by_user_id(_USER_ID)
        assert total == 2

    @pytest.mark.asyncio
    async def test_find_by_user_id_empty(self, repo: FakeLoanRepository) -> None:
        """find_by_user_id() gibt leere Liste zurück wenn keine Loans existieren."""
        loans, total = await repo.find_by_user_id(uuid.uuid4())
        assert total == 0
        assert list(loans) == []

    @pytest.mark.asyncio
    async def test_find_overdue_returns_active_past_due(
        self, repo: FakeLoanRepository
    ) -> None:
        """find_overdue() gibt nur ACTIVE Loans zurück deren due_date vergangen."""
        overdue = Loan(
            user_id=_USER_ID,
            isbn=_ISBN,
            due_date=date.today() - timedelta(days=1),
        )
        overdue.activate()
        not_due = _make_loan(LoanStatus.ACTIVE)
        await repo.save(overdue)
        await repo.save(not_due)
        result = await repo.find_overdue()
        assert len(list(result)) == 1
        assert list(result)[0].id == overdue.id

    @pytest.mark.asyncio
    async def test_save_updates_existing_loan(self, repo: FakeLoanRepository) -> None:
        """save() überschreibt einen vorhandenen Loan (z. B. nach Statuswechsel)."""
        loan = _make_loan()
        await repo.save(loan)
        loan.activate()
        await repo.save(loan)
        result = await repo.find_by_id(loan.id)
        assert result is not None
        assert result.status == LoanStatus.ACTIVE

