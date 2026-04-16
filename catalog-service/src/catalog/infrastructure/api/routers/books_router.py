"""Router for all /books-endpoints of Catalog Service."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from catalog.application.add_book_use_case import AddBookUseCase
from catalog.application.check_availability_use_case import CheckAvailabilityUseCase
from catalog.application.get_book_use_case import GetBookUseCase
from catalog.application.return_book_use_case import ReturnBookUseCase
from catalog.application.search_books_use_case import SearchBooksUseCase
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from catalog.domain.ports.book_stock_repository import BookStockRepository
from catalog.infrastructure.api.schemas.book_schema import (
    BookRequest,
    BookResponse,
    BooksListResponse,
    BookStockResponse,
)

router = APIRouter()


# ── Dependency functions ──────────────────────────────────────────────────────


def get_book_repo() -> BookRepository:
    """FastAPI dependency: provides a BookRepository per request.

    Replaced via dependency_overrides with a concrete implementation
    (tests: InMemoryBookRepository, production: SqlAlchemyBookRepository).

    Raises:
        RuntimeError: If no override has been registered.
    """
    raise RuntimeError(  # pragma: no cover
        "get_book_repo must be overridden via app.dependency_overrides"
    )


def get_stock_repo() -> BookStockRepository:
    """FastAPI dependency: provides a BookStockRepository per request.

    Raises:
        RuntimeError: If no override has been registered.
    """
    raise RuntimeError(  # pragma: no cover
        "get_stock_repo must be overridden via app.dependency_overrides"
    )


# ── GET /books ────────────────────────────────────────────────────────────────


@router.get(
    "/books",
    response_model=BooksListResponse,
    summary="List all books",
    response_description="A list of all books in the catalogue.",
)
async def get_books(
    q: str | None = Query(
        default=None, description="Search across title, author and genre"
    ),
    book_repo: BookRepository = Depends(get_book_repo),
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BooksListResponse:
    """Return books from the catalogue with optional full-text search (CAT-1).

    Searches title, author and genre simultaneously (OR logic).

    Args:
        q: Optional search term applied to title, author and genre.
        book_repo: Repository for book operations.
        stock_repo: Repository for stock operations.

    Returns:
        BooksListResponse containing matching books with available_count.
    """
    search_use_case = SearchBooksUseCase(book_repo)
    books, _ = await search_use_case.execute(
        title=q,
        author=q,
        genre=q,
    )
    availability_use_case = CheckAvailabilityUseCase(stock_repo)
    items: list[BookResponse] = []
    for book in books:
        try:
            count: int = await availability_use_case.execute(book.isbn)
        except ValueError:
            count = 0
        items.append(
            BookResponse(
                isbn=str(book.isbn),
                title=book.title,
                author=book.author,
                genre=book.genre,
                description=book.description,
                available_count=count,
            )
        )
    return BooksListResponse(items=items)


# ── POST /books ───────────────────────────────────────────────────────────────


@router.post(
    "/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a book",
    response_description="The newly created book.",
    responses={409: {"description": "A book with this ISBN already exists."}},
)
async def create_book(
    payload: BookRequest,
    book_repo: BookRepository = Depends(get_book_repo),
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookResponse:
    """Create a new book in the catalogue (CAT-3).

    Args:
        payload: Book data from the request body.
        book_repo: Repository for book operations.
        stock_repo: Repository for stock operations.

    Returns:
        The newly created book as a BookResponse.

    Raises:
        HTTPException: 409 Conflict if the ISBN already exists.
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


# ── GET /books/{isbn}/availability ────────────────────────────────────────────
# NOTE: Must be registered BEFORE GET /books/{isbn} so that Starlette matches
# the more specific route first (routes are matched in definition order).


@router.get(
    "/books/{isbn}/availability",
    response_model=BookStockResponse,
    summary="Check stock availability",
    response_description="Current available stock count for the given ISBN.",
    responses={
        404: {"description": "No stock entry found for this ISBN."},
        422: {"description": "The ISBN format is invalid."},
    },
)
async def get_availability(
    isbn: str,
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookStockResponse:
    """Return the current stock count for a book (CAT-2).

    Args:
        isbn: ISBN string from the URL path.
        stock_repo: Repository for stock operations.

    Returns:
        BookStockResponse with isbn and available_count.

    Raises:
        HTTPException: 404 if no stock entry was found.
        HTTPException: 422 if the ISBN is invalid.
    """
    try:
        isbn_vo = Isbn(isbn)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    use_case = CheckAvailabilityUseCase(stock_repo)
    try:
        count = await use_case.execute(isbn_vo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return BookStockResponse(isbn=str(isbn_vo), available_count=count)


# ── POST /books/{isbn}/return ─────────────────────────────────────────────────


@router.post(
    "/books/{isbn}/return",
    response_model=BookStockResponse,
    summary="Return a book",
    response_description="Updated stock after the return.",
    responses={
        404: {"description": "No stock entry found for this ISBN."},
        422: {"description": "The ISBN format is invalid."},
    },
)
async def return_book(
    isbn: str,
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookStockResponse:
    """Increase the book stock by 1 (CAT-6).

    Args:
        isbn: ISBN string from the URL path.
        stock_repo: Repository for stock operations.

    Returns:
        BookStockResponse with the updated available_count.

    Raises:
        HTTPException: 404 if no stock entry was found.
        HTTPException: 422 if the ISBN is invalid.
    """
    try:
        isbn_vo = Isbn(isbn)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    use_case = ReturnBookUseCase(stock_repo)
    try:
        stock = await use_case.execute(isbn=isbn_vo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return BookStockResponse(isbn=str(isbn_vo), available_count=stock.available_count)


# ── GET /books/{isbn} ─────────────────────────────────────────────────────────
# NOTE: Must be registered AFTER /books/{isbn}/availability and /books/{isbn}/return.


@router.get(
    "/books/{isbn}",
    response_model=BookResponse,
    summary="Get a book by ISBN",
    response_description="All metadata for the requested book.",
    responses={
        404: {"description": "No book found for this ISBN."},
        422: {"description": "The ISBN format is invalid."},
    },
)
async def get_book(
    isbn: str,
    book_repo: BookRepository = Depends(get_book_repo),
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookResponse:
    """Return a single book by ISBN including current availability (CAT-5).

    Args:
        isbn: ISBN string from the URL path.
        book_repo: Repository for book operations.
        stock_repo: Repository for stock operations.

    Returns:
        BookResponse with all book metadata and available_count.

    Raises:
        HTTPException: 404 if the book was not found.
        HTTPException: 422 if the ISBN is invalid.
    """
    try:
        isbn_vo = Isbn(isbn)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    use_case = GetBookUseCase(book_repo)
    try:
        book = await use_case.execute(isbn_vo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    try:
        count: int = await CheckAvailabilityUseCase(stock_repo).execute(isbn_vo)
    except ValueError:
        count = 0
    return BookResponse(
        isbn=str(book.isbn),
        title=book.title,
        author=book.author,
        genre=book.genre,
        description=book.description,
        available_count=count,
    )
