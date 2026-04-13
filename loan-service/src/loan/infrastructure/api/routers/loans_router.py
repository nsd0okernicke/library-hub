"""Router für alle /loans-Endpunkte des Loan Service."""
from fastapi import APIRouter, status

from loan.infrastructure.api.schemas.loan_schema import (
    LoanRequest,
    LoanResponse,
    LoansListResponse,
)

router = APIRouter()


@router.get("/loans", response_model=LoansListResponse)
async def get_loans(user_id: str) -> LoansListResponse:
    """Gibt alle Ausleihen eines Nutzers zurück.

    Args:
        user_id: ID des Nutzers, dessen Ausleihen abgerufen werden.

    Returns:
        LoansListResponse mit allen Ausleihen des Nutzers.
    """
    return LoansListResponse(items=[])


@router.post("/loans", response_model=LoanResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_loan(payload: LoanRequest) -> LoanResponse:
    """Legt eine neue Ausleih-Anfrage an.

    Args:
        payload: Ausleih-Daten aus dem Request-Body.

    Returns:
        LoanResponse mit der ID und dem Status der Ausleihe.
    """
    return LoanResponse(loan_id="dummy-id", status="PENDING")
