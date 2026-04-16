"""Router for all /loans endpoints of the Loan Service."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

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


# ── Dependency functions ──────────────────────────────────────────────────────


def get_loan_repo() -> LoanRepository:
    """FastAPI dependency: provides a LoanRepository per request.

    Returns:
        LoanRepository implementation.

    Raises:
        RuntimeError: If no override has been registered.
    """
    raise RuntimeError(
        "get_loan_repo must be overridden via dependency_overrides"
    )  # pragma: no cover


def get_publisher() -> MessagePublisher:
    """FastAPI dependency: provides a MessagePublisher per request.

    Returns:
        MessagePublisher implementation.

    Raises:
        RuntimeError: If no override has been registered.
    """
    raise RuntimeError(
        "get_publisher must be overridden via dependency_overrides"
    )  # pragma: no cover


# ── GET /loans ────────────────────────────────────────────────────────────────


@router.get(
    "/loans",
    response_model=LoansListResponse,
    summary="List loans for a user",
    response_description="All loans belonging to the given user.",
    responses={422: {"description": "user_id is not a valid UUID."}},
)
async def get_loans(
    user_id: str,
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoansListResponse:
    """Return all loans for a given user (LOAN-3).

    Args:
        user_id: UUID of the user as a string.
        loan_repo: Repository for loan operations.

    Returns:
        LoansListResponse containing all loans of the user.

    Raises:
        HTTPException: 422 if user_id is not a valid UUID.
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


@router.post(
    "/loans",
    response_model=LoanResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a book loan",
    response_description="The newly created loan with status PENDING.",
)
async def create_loan(
    payload: LoanRequest,
    loan_repo: LoanRepository = Depends(get_loan_repo),
    publisher: MessagePublisher = Depends(get_publisher),
) -> LoanResponse:
    """Create a new loan request and return 202 immediately (LOAN-1).

    Args:
        payload: Loan data from the request body.
        loan_repo: Repository for loan operations.
        publisher: Message publisher for events.

    Returns:
        LoanResponse with loan_id and status=PENDING.
    """
    use_case = RequestLoanUseCase(loan_repo, publisher)
    try:
        isbn = Isbn(payload.isbn)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    loan = await use_case.execute(isbn=isbn, user_id=payload.user_id)
    return LoanResponse(loan_id=str(loan.id), status=loan.status.value)


# ── GET /loans/overdue ────────────────────────────────────────────────────────


@router.get(
    "/loans/overdue",
    response_model=LoansListResponse,
    summary="List overdue loans",
    response_description="All active loans whose due date has passed.",
)
async def get_overdue_loans(
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoansListResponse:
    """Return all overdue loans (LOAN-5).

    Args:
        loan_repo: Repository for loan operations.

    Returns:
        LoansListResponse containing all overdue loans.
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


@router.get(
    "/loans/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Get a loan by ID",
    response_description="Full details of the requested loan.",
    responses={404: {"description": "Loan not found."}},
)
async def get_loan(
    loan_id: uuid.UUID,
    loan_repo: LoanRepository = Depends(get_loan_repo),
) -> LoanDetailResponse:
    """Return a single loan by ID (LOAN-2).

    Args:
        loan_id: UUID of the loan.
        loan_repo: Repository for loan operations.

    Returns:
        LoanDetailResponse with all loan fields.

    Raises:
        HTTPException: 404 if the loan does not exist.
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


# ── POST /loans/{loan_id}/return ──────────────────────────────────────────────


@router.post(
    "/loans/{loan_id}/return",
    response_model=LoanDetailResponse,
    summary="Return a book",
    response_description="Loan with status RETURNED.",
    responses={
        404: {"description": "Loan not found."},
        409: {"description": "Loan is not active or already returned."},
    },
)
async def return_loan(
    loan_id: uuid.UUID,
    loan_repo: LoanRepository = Depends(get_loan_repo),
    publisher: MessagePublisher = Depends(get_publisher),
) -> LoanDetailResponse:
    """Return a book (ACTIVE → RETURNED) and publish BookReturned (LOAN-4).

    Args:
        loan_id: UUID of the loan.
        loan_repo: Repository for loan operations.
        publisher: Message publisher for events.

    Returns:
        LoanDetailResponse with status=RETURNED.

    Raises:
        HTTPException: 404 if not found, 409 on invalid status transition.
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
