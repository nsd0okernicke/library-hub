"""Application Use Case: SearchBooksUseCase (Catalog Service).

Implements CAT-1 – Search, filter and paginate books.
"""

from __future__ import annotations

from collections.abc import Sequence

from catalog.domain.book import Book
from catalog.domain.ports.book_repository import BookRepository


class SearchBooksUseCase:
    """Search, filter and paginate Books from the catalogue."""

    def __init__(self, book_repo: BookRepository) -> None:
        self._book_repo = book_repo

    async def execute(
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Book], int]:
        """Return a filtered and paginated list of Books.

        Args:
            title: Optional case-insensitive title substring filter.
            author: Optional case-insensitive author substring filter.
            genre: Optional case-insensitive genre substring filter.
            page: 1-based page number.
            page_size: Items per page.

        Returns:
            Tuple of (items, total_count).
        """
        return await self._book_repo.find_all(
            title=title,
            author=author,
            genre=genre,
            page=page,
            page_size=page_size,
        )

