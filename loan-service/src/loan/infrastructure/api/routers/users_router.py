"""Router for all /users endpoints of the Loan Service."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from loan.application.get_user_by_email_use_case import GetUserByEmailUseCase
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
    raise RuntimeError("get_user_repo must be overridden via dependency_overrides")  # pragma: no cover


# ── POST /users ───────────────────────────────────────────────────────────────

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    response_description="The newly created user.",
    responses={409: {"description": "A user with this e-mail already exists."}},
)
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


# ── GET /users ────────────────────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=UserResponse,
    summary="Look up a user by e-mail",
    response_description="The user matching the given e-mail address.",
    responses={404: {"description": "No user found for this e-mail address."}},
)
async def get_user_by_email(
    email: str = Query(description="E-mail address to look up"),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    """Return a user by e-mail address (login lookup).

    Args:
        email: E-mail address passed as a query parameter.
        user_repo: Repository for user operations.

    Returns:
        UserResponse with id, name and email.

    Raises:
        HTTPException: 404 if no user with that e-mail exists.
    """
    use_case = GetUserByEmailUseCase(user_repo)
    try:
        user = await use_case.execute(email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return UserResponse(id=user.id, name=user.name, email=user.email)


