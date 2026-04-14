"""API tests for all endpoints of the Loan Service.

Uses dependency overrides with in-memory fake repositories (via conftest.py)
so that no real database setup is required.
"""
import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from loan.application.activate_loan_use_case import ActivateLoanUseCase
from loan.application.reject_loan_use_case import RejectLoanUseCase
from loan.main import app
from tests.api.conftest import get_current_loan_repo

ISBN_VALID = "978-3-16-148410-0"
USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # fixed UUID for deterministic tests


# ── GET /loans (LOAN-3) ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_loans_returns_200_and_list() -> None:
    """GET /loans returns 200 OK and an empty list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/loans?user_id={USER_ID}")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_get_loans_missing_user_id_returns_422() -> None:
    """GET /loans without user_id returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/loans")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_loans_invalid_user_id_returns_422() -> None:
    """GET /loans with a non-UUID user_id returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/loans?user_id=not-a-uuid")
    assert response.status_code == 422


# ── POST /loans (LOAN-1) ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_loans_creates_loan() -> None:
    """POST /loans creates a new loan request and returns 202."""
    payload = {"isbn": ISBN_VALID, "user_id": str(uuid.uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/loans", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "loan_id" in data
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_post_loans_missing_fields_returns_422() -> None:
    """POST /loans without required fields returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/loans", json={"isbn": ISBN_VALID})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_loans_invalid_isbn_returns_422() -> None:
    """POST /loans with an invalid ISBN format returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/loans", json={"isbn": "NOT-AN-ISBN", "user_id": str(uuid.uuid4())}
        )
    assert response.status_code == 422


# ── POST /users (LOAN-0) ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_users_creates_user() -> None:
    """POST /users creates a new user and returns 201."""
    payload = {"name": "Alice Müller", "email": "alice@example.com"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_post_users_duplicate_email_returns_409() -> None:
    """POST /users with a duplicate e-mail returns 409."""
    payload = {"name": "Alice Müller", "email": "alice@example.com"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/users", json=payload)
        response = await ac.post("/users", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_post_users_missing_fields_returns_422() -> None:
    """POST /users without required fields returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/users", json={"name": "Alice"})
    assert response.status_code == 422


# ── GET /loans/{loan_id} (LOAN-2) ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_loan_by_id_returns_200() -> None:
    """GET /loans/{loan_id} returns 200 OK and loan data."""
    payload = {"isbn": ISBN_VALID, "user_id": str(uuid.uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_resp = await ac.post("/loans", json=payload)
        loan_id = create_resp.json()["loan_id"]
        response = await ac.get(f"/loans/{loan_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["loan_id"] == loan_id
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_loan_by_id_unknown_returns_404() -> None:
    """GET /loans/{loan_id} with unknown ID returns 404."""
    unknown_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/loans/{unknown_id}")
    assert response.status_code == 404


# ── POST /loans/{loan_id}/activate – endpoint removed ────────────────────────
# Activation is now exclusively event-driven via BookReserved RabbitMQ message.
# The endpoint no longer exists; 404 is expected for any call to it.

@pytest.mark.asyncio
async def test_activate_endpoint_no_longer_exists() -> None:
    """POST /loans/{loan_id}/activate returns 404 – endpoint was removed."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/loans/{uuid.uuid4()}/activate")
    assert response.status_code == 404


# ── POST /loans/{loan_id}/return (LOAN-4) ─────────────────────────────────────
# Return tests activate the loan directly via ActivateLoanUseCase on the shared
# in-memory repo, mirroring what the RabbitmqConsumer does in production.

async def _activate_via_use_case(loan_id: str) -> None:
    """Simulate a BookReserved event by calling ActivateLoanUseCase directly."""
    repo = get_current_loan_repo()
    await ActivateLoanUseCase(loan_repo=repo).execute(loan_id=uuid.UUID(loan_id))


@pytest.mark.asyncio
async def test_return_loan_returns_200() -> None:
    """POST /loans/{loan_id}/return returns 200 (ACTIVE → RETURNED)."""
    payload = {"isbn": ISBN_VALID, "user_id": str(uuid.uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_resp = await ac.post("/loans", json=payload)
        loan_id = create_resp.json()["loan_id"]
        await _activate_via_use_case(loan_id)
        response = await ac.post(f"/loans/{loan_id}/return")
    assert response.status_code == 200
    assert response.json()["status"] == "RETURNED"


@pytest.mark.asyncio
async def test_return_loan_unknown_id_returns_404() -> None:
    """POST /loans/{loan_id}/return with unknown ID returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/loans/{uuid.uuid4()}/return")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_return_loan_already_returned_returns_409() -> None:
    """POST /loans/{loan_id}/return twice returns 409."""
    payload = {"isbn": ISBN_VALID, "user_id": str(uuid.uuid4())}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_resp = await ac.post("/loans", json=payload)
        loan_id = create_resp.json()["loan_id"]
        await _activate_via_use_case(loan_id)
        await ac.post(f"/loans/{loan_id}/return")
        response = await ac.post(f"/loans/{loan_id}/return")

    assert response.status_code == 409


# ── GET /loans/overdue (LOAN-5) ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_overdue_loans_returns_200_and_list() -> None:
    """GET /loans/overdue returns 200 OK and a list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/loans/overdue")
    assert response.status_code == 200
    assert "items" in response.json()

