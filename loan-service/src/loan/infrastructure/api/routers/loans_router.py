"""Router für alle /loans-Endpunkte des Loan Service."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from loan.application.activate_loan_use_case import ActivateLoanUseCase
from loan.application.get_loan_use_case import GetLoanUseCase
from loan.application.list_loans_use_case import ListLoansUseCase
from loan.application.list_overdue_loans_use_case import ListOverdueLoansUseCase
from loan.application.request_loan_use_case import RequestLoanUseCase
from loan.application.return_loan_use_case import ReturnLoanUseCase
from loan.domain.isbn import Isbn
from loan.domain.ports.loan_repository import LoanRepository
from loan.domain.ports.message_publisher import MessagePublisher
from loan.infrastructure.api.schemas.loan_schema import (
    LoanDetailResponse,
    LoanRequest,
    LoanResponse,
    LoansListResponse,
)

router = APIRouter()


# ── Dependency-Funktionen ─────────────────────────────────────────────────────

def get_loan_repo() -> LoanRepository:
    """FastAPI-Dependency: liefert ein LoanRepository pro Request.

    Returns:
        LoanRepository-Implementierung.

    Raises:
        RuntimeError: Wenn kein Override gesetzt ist (nur in Tests relevant).
    """
    raise RuntimeError("get_loan_repo must be overridden via dependency_overrides")


def get_publisher() -> MessagePublisher:
    """FastAPI-Dependency: liefert einen MessagePublisher pro Request.

    Returns:
        MessagePublisher-Implementierung.

    Raises:
        RuntimeError: Wenn kein Override gesetzt ist.
    """
    raise RuntimeError("get_publisher must be overridden via dependency_overrides")


# ── GET /loans ────────────────────────────────────────────────────────────────

@router.get("/loans", response_model=LoansListResponse)
async def get_loans(
    user_id: str,
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoansListResponse:
    """Gibt alle Ausleihen eines Nutzers zurück (LOAN-3).

    Args:
        user_id: UUID des Nutzers als String.
        loan_repo: Repository für Ausleihoperationen.

    Returns:
        LoansListResponse mit allen Ausleihen des Nutzers.

    Raises:
        HTTPException: 422 wenn user_id keine gültige UUID ist.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid user_id: '{user_id}' is not a valid UUID",
        )
    use_case = ListLoansUseCase(loan_repo)
    loans, _ = await use_case.execute(user_id=user_uuid)
    return LoansListResponse(
        items=[
            LoanDetailResponse(
                loan_id=loan.id,
                isbn=str(loan.isbn),
                user_id=loan.user_id,
                status=loan.status.value,
                due_date=loan.due_date,
                returned_at=loan.returned_at,
            )
            for loan in loans
        ]
    )


# ── POST /loans ───────────────────────────────────────────────────────────────

@router.post("/loans", response_model=LoanResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_loan(
    payload: LoanRequest,
    loan_repo: LoanRepository = Depends(get_loan_repo),
    publisher: MessagePublisher = Depends(get_publisher),
) -> LoanResponse:
    """Legt eine neue Ausleih-Anfrage an und gibt sofort 202 zurück (LOAN-1).

    Args:
        payload: Ausleih-Daten aus dem Request-Body.
        loan_repo: Repository für Ausleihoperationen.
        publisher: Message-Publisher für Events.

    Returns:
        LoanResponse mit loan_id und status=PENDING.
    """
    use_case = RequestLoanUseCase(loan_repo, publisher)
    loan = await use_case.execute(isbn=Isbn(payload.isbn), user_id=payload.user_id)
    return LoanResponse(loan_id=str(loan.id), status=loan.status.value)


# ── GET /loans/overdue ────────────────────────────────────────────────────────

@router.get("/loans/overdue", response_model=LoansListResponse)
async def get_overdue_loans(
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoansListResponse:
    """Gibt alle überfälligen Ausleihen zurück (LOAN-5).

    Args:
        loan_repo: Repository für Ausleihoperationen.

    Returns:
        LoansListResponse mit allen überfälligen Ausleihen.
    """
    use_case = ListOverdueLoansUseCase(loan_repo)
    loans = await use_case.execute()
    return LoansListResponse(
        items=[
            LoanDetailResponse(
                loan_id=loan.id,
                isbn=str(loan.isbn),
                user_id=loan.user_id,
                status=loan.status.value,
                due_date=loan.due_date,
                returned_at=loan.returned_at,
            )
            for loan in loans
        ]
    )


# ── GET /loans/{loan_id} ──────────────────────────────────────────────────────

@router.get("/loans/{loan_id}", response_model=LoanDetailResponse)
async def get_loan(
    loan_id: uuid.UUID,
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoanDetailResponse:
    """Gibt eine einzelne Ausleihe per ID zurück (LOAN-2).

    Args:
        loan_id: UUID der Ausleihe.
        loan_repo: Repository für Ausleihoperationen.

    Returns:
        LoanDetailResponse mit allen Feldern der Ausleihe.

    Raises:
        HTTPException: 404 wenn die Ausleihe nicht existiert.
    """
    use_case = GetLoanUseCase(loan_repo)
    try:
        loan = await use_case.execute(loan_id=loan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return LoanDetailResponse(
        loan_id=loan.id,
        isbn=str(loan.isbn),
        user_id=loan.user_id,
        status=loan.status.value,
        due_date=loan.due_date,
        returned_at=loan.returned_at,
    )


# ── POST /loans/{loan_id}/activate ────────────────────────────────────────────

@router.post("/loans/{loan_id}/activate", response_model=LoanDetailResponse)
async def activate_loan(
    loan_id: uuid.UUID,
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoanDetailResponse:
    """Aktiviert eine Ausleihe (PENDING → ACTIVE).

    Wird intern durch den BookReserved-Event-Consumer aufgerufen.

    Args:
        loan_id: UUID der Ausleihe.
        loan_repo: Repository für Ausleihoperationen.

    Returns:
        LoanDetailResponse mit status=ACTIVE.

    Raises:
        HTTPException: 404 wenn nicht gefunden, 409 bei ungültigem Übergang.
    """
    use_case = ActivateLoanUseCase(loan_repo)
    try:
        loan = await use_case.execute(loan_id=loan_id)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
    return LoanDetailResponse(
        loan_id=loan.id,
        isbn=str(loan.isbn),
        user_id=loan.user_id,
        status=loan.status.value,
        due_date=loan.due_date,
        returned_at=loan.returned_at,
    )


# ── POST /loans/{loan_id}/return ──────────────────────────────────────────────

@router.post("/loans/{loan_id}/return", response_model=LoanDetailResponse)
async def return_loan(
    loan_id: uuid.UUID,
    loan_repo: LoanRepository = Depends(get_loan_repo),
    publisher: MessagePublisher = Depends(get_publisher),
) -> LoanDetailResponse:
    """Gibt ein Buch zurück (ACTIVE → RETURNED) und publiziert BookReturned (LOAN-4).

    Args:
        loan_id: UUID der Ausleihe.
        loan_repo: Repository für Ausleihoperationen.
        publisher: Message-Publisher für Events.

    Returns:
        LoanDetailResponse mit status=RETURNED.

    Raises:
        HTTPException: 404 wenn nicht gefunden, 409 bei ungültigem Übergang.
    """
    use_case = ReturnLoanUseCase(loan_repo, publisher)
    try:
        loan = await use_case.execute(loan_id=loan_id)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
    return LoanDetailResponse(
        loan_id=loan.id,
        isbn=str(loan.isbn),
        user_id=loan.user_id,
        status=loan.status.value,
        due_date=loan.due_date,
        returned_at=loan.returned_at,
    )

