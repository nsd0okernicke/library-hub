"""Loan Service – FastAPI application entry point."""

from fastapi import FastAPI

from loan.infrastructure.api.routers.loans_router import (
    router as loans_router,
    get_loan_repo,
    get_publisher,
)
from loan.infrastructure.api.routers.users_router import (
    router as users_router,
    get_user_repo,
)

app = FastAPI(
    title="LibraryHub – Loan Service",
    version="0.1.0",
    description="Manages loan transactions and users.",
)

# Produktive Implementierungen werden später via DB-Session verdrahtet.
# Im MVP bleiben die Overrides für Tests zuständig; für Produktion wird
# analog zu catalog-service ein _prod_*-Override gesetzt sobald DB vorhanden.

app.include_router(loans_router)
app.include_router(users_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A simple status dict.
    """
    return {"status": "ok", "service": "loan-service"}

