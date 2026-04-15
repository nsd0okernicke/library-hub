"""Pydantic schemas for Book objects (API layer).

Separates request and response schemas following Clean Architecture.
"""
from typing import Optional

from pydantic import BaseModel


class BookRequest(BaseModel):
    """Schema for incoming book requests (POST /books).

    Attributes:
        isbn: ISBN string (10 or 13 digits, hyphens allowed).
        title: Book title.
        author: Full author name.
        genre: Genre or subject area.
        initial_stock: Initial stock count (≥ 0).
        description: Optional free-text description.
    """

    isbn: str
    title: str
    author: str
    genre: str
    initial_stock: int
    description: Optional[str] = None


class BookResponse(BaseModel):
    """Schema for outgoing book responses.

    Attributes:
        isbn: ISBN string.
        title: Book title.
        author: Full author name.
        genre: Genre or subject area.
        description: Optional free-text description.
        available_count: Current available stock (None when not fetched).
    """

    model_config = {"from_attributes": True}

    isbn: str
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    available_count: Optional[int] = None


class BooksListResponse(BaseModel):
    """Schema for a paginated list of books.

    Attributes:
        items: List of book response objects.
    """

    items: list


class BookStockResponse(BaseModel):
    """Schema for stock responses (GET /availability, POST /return).

    Attributes:
        isbn: ISBN string.
        available_count: Currently available copies.
    """

    isbn: str
    available_count: int
