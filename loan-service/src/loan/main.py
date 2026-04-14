"""Loan Service – FastAPI application entry point."""

from fastapi import FastAPI

from loan.infrastructure.api.routers.loans_router import (
    get_loan_repo,
    get_publisher,
    router as loans_router,
)
from loan.infrastructure.api.routers.users_router import (
    get_user_repo,
    router as users_router,
)

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="LibraryHub – Loan Service",
    version="0.1.0",
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

