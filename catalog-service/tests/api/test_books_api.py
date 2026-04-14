"""API tests for all endpoints of the Catalog Service.

Uses dependency overrides with in-memory fake repositories (via conftest.py)
so that no real database setup is required.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from catalog.main import app

ISBN_VALID = "978-3-16-148410-0"
ISBN_UNKNOWN = "978-0-7432-7356-5"
ISBN_INVALID = "NOT-AN-ISBN"


# ── Helper ────────────────────────────────────────────────────────────────────

async def _create_book(ac: AsyncClient, isbn: str = ISBN_VALID, initial_stock: int = 3) -> None:
    """Create a test book via POST /books."""
    await ac.post("/books", json={
        "isbn": isbn,
        "title": "Test Book",
        "author": "Test Author",
        "genre": "Fiction",
        "initial_stock": initial_stock,
    })


# ── GET /books ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_books_returns_200_and_list() -> None:
    """GET /books gibt 200 OK und eine leere Liste zurück."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/books")
    assert response.status_code == 200
    assert "items" in response.json()
    assert response.json()["items"] == []


# ── POST /books ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_books_creates_book() -> None:
    """POST /books legt ein neues Buch an und gibt 201 zurück."""
    payload = {
        "isbn": ISBN_VALID,
        "title": "Testbuch",
        "author": "Autor",
        "genre": "Roman",
        "initial_stock": 3,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/books", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["isbn"] == payload["isbn"]
    assert data["title"] == payload["title"]
    assert data["author"] == payload["author"]
    assert data["genre"] == payload["genre"]


@pytest.mark.asyncio
async def test_post_books_duplicate_isbn_returns_409() -> None:
    """POST /books mit doppelter ISBN gibt 409 Conflict zurück."""
    payload = {
        "isbn": ISBN_VALID,
        "title": "Testbuch",
        "author": "Autor",
        "genre": "Roman",
        "initial_stock": 1,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/books", json=payload)
        response = await ac.post("/books", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_post_books_missing_fields_returns_422() -> None:
    """POST /books ohne Pflichtfelder gibt 422 zurück."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/books", json={"isbn": ISBN_VALID})
    assert response.status_code == 422


# ── GET /books/{isbn} (CAT-5) ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_book_by_isbn_returns_200() -> None:
    """GET /books/{isbn} gibt 200 OK + Buchdaten zurück."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await _create_book(ac)
        response = await ac.get(f"/books/{ISBN_VALID}")
    assert response.status_code == 200
    data = response.json()
    assert data["isbn"] == ISBN_VALID
    assert data["title"] == "Test Book"


@pytest.mark.asyncio
async def test_get_book_by_isbn_unknown_returns_404() -> None:
    """GET /books/{isbn} with unknown ISBN returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/books/{ISBN_UNKNOWN}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_book_by_isbn_invalid_returns_422() -> None:
    """GET /books/{isbn} with invalid ISBN format returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/books/NOT-AN-ISBN")
    assert response.status_code == 422


# ── GET /books/{isbn}/availability (CAT-2) ────────────────────────────────────

@pytest.mark.asyncio
async def test_get_availability_returns_200_with_count() -> None:
    """GET /books/{isbn}/availability gibt 200 OK + available_count zurück."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await _create_book(ac, initial_stock=5)
        response = await ac.get(f"/books/{ISBN_VALID}/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["isbn"] == ISBN_VALID
    assert data["available_count"] == 5


@pytest.mark.asyncio
async def test_get_availability_unknown_isbn_returns_404() -> None:
    """GET /books/{isbn}/availability with unknown ISBN returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/books/{ISBN_UNKNOWN}/availability")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_availability_invalid_isbn_returns_422() -> None:
    """GET /books/{isbn}/availability with invalid ISBN format returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/books/NOT-AN-ISBN/availability")
    assert response.status_code == 422


# ── POST /books/{isbn}/return (CAT-6) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_return_book_increases_stock() -> None:
    """POST /books/{isbn}/return increases the stock by 1 and returns 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await _create_book(ac, initial_stock=2)
        response = await ac.post(f"/books/{ISBN_VALID}/return")
    assert response.status_code == 200
    data = response.json()
    assert data["isbn"] == ISBN_VALID
    assert data["available_count"] == 3


@pytest.mark.asyncio
async def test_return_book_unknown_isbn_returns_404() -> None:
    """POST /books/{isbn}/return with unknown ISBN returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/books/{ISBN_UNKNOWN}/return")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_return_book_invalid_isbn_returns_422() -> None:
    """POST /books/{isbn}/return with invalid ISBN format returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/books/NOT-AN-ISBN/return")
    assert response.status_code == 422

