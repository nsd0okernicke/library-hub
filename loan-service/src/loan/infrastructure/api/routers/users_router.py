"""Router für alle /users-Endpunkte des Loan Service."""
from fastapi import APIRouter, Depends, HTTPException, status

from loan.application.register_user_use_case import RegisterUserUseCase
from loan.domain.ports.user_repository import UserRepository
from loan.infrastructure.api.schemas.user_schema import UserRequest, UserResponse

router = APIRouter()


# ── Dependency-Funktionen ─────────────────────────────────────────────────────

def get_user_repo() -> UserRepository:
    """FastAPI-Dependency: liefert ein UserRepository pro Request.

    Returns:
        UserRepository-Implementierung.

    Raises:
        RuntimeError: Wenn kein Override gesetzt ist.
    """
    raise RuntimeError("get_user_repo must be overridden via dependency_overrides")


# ── POST /users ───────────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    """Legt einen neuen Nutzer an (LOAN-0).

    Args:
        payload: Nutzerdaten aus dem Request-Body.
        user_repo: Repository für Nutzeroperationen.

    Returns:
        UserResponse mit id, name und email.

    Raises:
        HTTPException: 409 Conflict wenn die E-Mail bereits registriert ist.
    """
    use_case = RegisterUserUseCase(user_repo)
    try:
        user = await use_case.execute(name=payload.name, email=payload.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return UserResponse(id=user.id, name=user.name, email=user.email)

