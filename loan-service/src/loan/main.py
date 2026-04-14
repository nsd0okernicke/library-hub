"""Loan Service – FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from loan.infrastructure.api.routers.loans_router import (
    get_loan_repo,
    get_publisher,
    router as loans_router,
)
from loan.infrastructure.api.routers.users_router import (
    get_user_repo,
    router as users_router,
)
from loan.infrastructure.db.models import Base
from loan.infrastructure.db.session import engine, get_session
from loan.infrastructure.db.sqlalchemy_loan_repository import SqlAlchemyLoanRepository
from loan.infrastructure.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from loan.infrastructure.messaging.logging_publisher import LoggingMessagePublisher


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create all DB tables on startup (dev convenience – replace with Alembic later).

    Args:
        app: The FastAPI application instance.

    Yields:
        None – runs shutdown logic after yield.
    """
    async with engine.begin() as conn:  # pragma: no cover
        await conn.run_sync(Base.metadata.create_all)  # pragma: no cover
    yield  # pragma: no cover


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="LibraryHub – Loan Service",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "Manages loan transactions and user registration for the LibraryHub system.\n\n"
        "## Features\n"
        "- Register new library users\n"
        "- Request, activate, reject and return book loans\n"
        "- List loans per user and overdue loans\n\n"
        "## Event-driven integration\n"
        "Publishes `BookLoanRequested` / `BookReturned` events and consumes "
        "`BookReserved` / `BookOutOfStock` events via RabbitMQ."
    ),
    contact={
        "name": "LibraryHub Team",
        "url": "https://github.com/your-org/library-hub",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "users",
            "description": "User registration and management.",
        },
        {
            "name": "loans",
            "description": (
                "Loan lifecycle operations – request, activate, reject, "
                "return and query loans."
            ),
        },
        {
            "name": "health",
            "description": "Service health check.",
        },
    ],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(loans_router, tags=["loans"])
app.include_router(users_router, tags=["users"])


# ── Production dependency overrides ──────────────────────────────────────────

def _prod_user_repo(  # pragma: no cover
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyUserRepository:
    """Production UserRepository implementation (SQLAlchemy)."""
    return SqlAlchemyUserRepository(session)


def _prod_loan_repo(  # pragma: no cover
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyLoanRepository:
    """Production LoanRepository implementation (SQLAlchemy)."""
    return SqlAlchemyLoanRepository(session)


def _prod_publisher() -> LoggingMessagePublisher:  # pragma: no cover
    """Development MessagePublisher (logs instead of sending to RabbitMQ)."""
    return LoggingMessagePublisher()


app.dependency_overrides[get_user_repo] = _prod_user_repo
app.dependency_overrides[get_loan_repo] = _prod_loan_repo
app.dependency_overrides[get_publisher] = _prod_publisher


# ── Health ────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    response_description="Service status and name.",
)
async def health() -> dict[str, str]:
    """Return the current health status of the Loan Service.

    Returns:
        A dict with ``status`` and ``service`` keys.
    """
    return {"status": "ok", "service": "loan-service"}

