"""Router for all /users endpoints of the Loan Service."""
from fastapi import APIRouter, Depends, HTTPException, status

from loan.application.register_user_use_case import RegisterUserUseCase
from loan.domain.ports.user_repository import UserRepository
from loan.infrastructure.api.schemas.user_schema import UserRequest, UserResponse

router = APIRouter()


# ── Dependency functions ──────────────────────────────────────────────────────

def get_user_repo() -> UserRepository:
    """FastAPI dependency: provides a UserRepository per request.

    Returns:
        UserRepository implementation.

    Raises:
        RuntimeError: If no override has been registered.
    """
    raise RuntimeError("get_user_repo must be overridden via dependency_overrides")


# ── POST /users ───────────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    """Create a new user (LOAN-0).

    Args:
        payload: User data from the request body.
        user_repo: Repository for user operations.

    Returns:
        UserResponse with id, name and email.

    Raises:
        HTTPException: 409 Conflict if the e-mail is already registered.
    """
    use_case = RegisterUserUseCase(user_repo)
    try:
        user = await use_case.execute(name=payload.name, email=payload.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return UserResponse(id=user.id, name=user.name, email=user.email)
