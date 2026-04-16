"""API tests for /users endpoints of the Loan Service."""
import pytest
from httpx import AsyncClient, ASGITransport

from loan.main import app

EMAIL = "alice@example.com"
NAME = "Alice"


# ── Helper ────────────────────────────────────────────────────────────────────

async def _register_user(ac: AsyncClient, email: str = EMAIL, name: str = NAME) -> dict:
    """Register a user via POST /users and return the response body."""
    res = await ac.post("/users", json={"name": name, "email": email})
    assert res.status_code == 201
    return res.json()


# ── POST /users ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_user_returns_201() -> None:
    """POST /users creates a new user and returns 201."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/users", json={"name": NAME, "email": EMAIL})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == NAME
    assert data["email"] == EMAIL
    assert "id" in data


@pytest.mark.asyncio
async def test_register_user_duplicate_email_returns_409() -> None:
    """POST /users with a duplicate e-mail returns 409 Conflict."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await _register_user(ac)
        response = await ac.post("/users", json={"name": NAME, "email": EMAIL})
    assert response.status_code == 409


# ── GET /users?email= ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_user_by_email_returns_200() -> None:
    """GET /users?email= returns 200 and user data for a registered e-mail."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        created = await _register_user(ac)
        response = await ac.get(f"/users?email={EMAIL}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == NAME
    assert data["email"] == EMAIL


@pytest.mark.asyncio
async def test_get_user_by_email_unknown_returns_404() -> None:
    """GET /users?email= returns 404 when the e-mail is not registered."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/users?email=unknown@example.com")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_by_email_missing_param_returns_422() -> None:
    """GET /users without email query param returns 422 Unprocessable Entity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/users")
    assert response.status_code == 422

