"""Router für alle /books-Endpunkte des Catalog Service."""
from collections.abc import AsyncGenerator

from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.application.add_book_use_case import AddBookUseCase
from catalog.application.search_books_use_case import SearchBooksUseCase
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from catalog.domain.ports.book_stock_repository import BookStockRepository
from catalog.infrastructure.api.schemas.book_schema import (
    BookRequest,
    BookResponse,
    BooksListResponse,
)
from catalog.infrastructure.db.session import get_session
from catalog.infrastructure.db.sqlalchemy_book_repository import SqlAlchemyBookRepository
from catalog.infrastructure.db.sqlalchemy_book_stock_repository import SqlAlchemyBookStockRepository

router = APIRouter()


def get_book_repo(session: AsyncSession = Depends(get_session)) -> BookRepository:
    """FastAPI-Dependency: liefert ein BookRepository pro Request.

    Args:
        session: Aktive SQLAlchemy-AsyncSession.

    Returns:
        BookRepository-Implementierung (SqlAlchemy).
    """
    return SqlAlchemyBookRepository(session)


def get_stock_repo(session: AsyncSession = Depends(get_session)) -> BookStockRepository:
    """FastAPI-Dependency: liefert ein BookStockRepository pro Request.

    Args:
        session: Aktive SQLAlchemy-AsyncSession.

    Returns:
        BookStockRepository-Implementierung (SqlAlchemy).
    """
    return SqlAlchemyBookStockRepository(session)


@router.get("/books", response_model=BooksListResponse)
async def get_books(
    book_repo: BookRepository = Depends(get_book_repo),
) -> BooksListResponse:
    """Gibt alle Bücher aus dem Katalog zurück.

    Returns:
        BooksListResponse mit allen vorhandenen Büchern.
    """
    use_case = SearchBooksUseCase(book_repo)
    books, _ = await use_case.execute()
    return BooksListResponse(
        items=[
            BookResponse(
                isbn=str(book.isbn),
                title=book.title,
                author=book.author,
                genre=book.genre,
                description=book.description,
            )
            for book in books
        ]
    )


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookRequest,
    book_repo: BookRepository = Depends(get_book_repo),
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookResponse:
    """Legt ein neues Buch im Katalog an.

    Args:
        payload: Buchdaten aus dem Request-Body.
        book_repo: Repository für Buchoperationen.
        stock_repo: Repository für Bestandsoperationen.

    Returns:
        Das neu angelegte Buch als BookResponse.

    Raises:
        HTTPException: 409 Conflict, wenn die ISBN bereits existiert.
    """
    use_case = AddBookUseCase(book_repo, stock_repo)
    try:
        book = await use_case.execute(
            isbn=Isbn(payload.isbn),
            title=payload.title,
            author=payload.author,
            genre=payload.genre,
            initial_stock=payload.initial_stock,
            description=payload.description,
        )
        return BookResponse(
            isbn=str(book.isbn),
            title=book.title,
            author=book.author,
            genre=book.genre,
            description=book.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
