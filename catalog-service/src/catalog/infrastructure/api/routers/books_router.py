"""Router für alle /books-Endpunkte des Catalog Service."""
from fastapi import APIRouter, status, HTTPException, Depends

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
    BookStockResponse,
    BooksListResponse,
)

router = APIRouter()


# ── Dependency-Funktionen ─────────────────────────────────────────────────────

def get_book_repo() -> BookRepository:
    """FastAPI-Dependency: liefert ein BookRepository pro Request.

    Wird via dependency_overrides durch eine konkrete Implementierung ersetzt
    (Tests: InMemoryBookRepository, Produktion: SqlAlchemyBookRepository).

    Raises:
        RuntimeError: Wenn kein Override gesetzt ist.
    """
    raise RuntimeError(  # pragma: no cover
        "get_book_repo must be overridden via app.dependency_overrides"
    )


def get_stock_repo() -> BookStockRepository:
    """FastAPI-Dependency: liefert ein BookStockRepository pro Request.

    Raises:
        RuntimeError: Wenn kein Override gesetzt ist.
    """
    raise RuntimeError(  # pragma: no cover
        "get_stock_repo must be overridden via app.dependency_overrides"
    )


# ── GET /books ────────────────────────────────────────────────────────────────

@router.get("/books", response_model=BooksListResponse)
async def get_books(
    book_repo: BookRepository = Depends(get_book_repo),
) -> BooksListResponse:
    """Gibt alle Bücher aus dem Katalog zurück (CAT-1).

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


# ── POST /books ───────────────────────────────────────────────────────────────

@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookRequest,
    book_repo: BookRepository = Depends(get_book_repo),
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookResponse:
    """Legt ein neues Buch im Katalog an (CAT-3).

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


# ── GET /books/{isbn}/availability ────────────────────────────────────────────
# WICHTIG: Muss VOR GET /books/{isbn} stehen, damit FastAPI die spezifischere
# Route korrekt matched (Starlette matched in Definitionsreihenfolge).

@router.get("/books/{isbn}/availability", response_model=BookStockResponse)
async def get_availability(
    isbn: str,
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookStockResponse:
    """Gibt den aktuellen Bestand eines Buches zurück (CAT-2).

    Args:
        isbn: ISBN-Zeichenkette aus dem URL-Pfad.
        stock_repo: Repository für Bestandsoperationen.

    Returns:
        BookStockResponse mit isbn und available_count.

    Raises:
        HTTPException: 404 wenn kein Bestandseintrag gefunden wurde.
        HTTPException: 422 wenn die ISBN ungültig ist.
    """
    try:
        isbn_vo = Isbn(isbn)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    use_case = CheckAvailabilityUseCase(stock_repo)
    try:
        count = await use_case.execute(isbn_vo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return BookStockResponse(isbn=str(isbn_vo), available_count=count)


# ── POST /books/{isbn}/return ─────────────────────────────────────────────────

@router.post("/books/{isbn}/return", response_model=BookStockResponse)
async def return_book(
    isbn: str,
    stock_repo: BookStockRepository = Depends(get_stock_repo),
) -> BookStockResponse:
    """Increases the book stock by 1 (CAT-6).

    Args:
        isbn: ISBN-Zeichenkette aus dem URL-Pfad.
        stock_repo: Repository für Bestandsoperationen.

    Returns:
        BookStockResponse mit aktualisiertem available_count.

    Raises:
        HTTPException: 404 wenn kein Bestandseintrag gefunden wurde.
        HTTPException: 422 wenn die ISBN ungültig ist.
    """
    try:
        isbn_vo = Isbn(isbn)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    use_case = ReturnBookUseCase(stock_repo)
    try:
        stock = await use_case.execute(isbn=isbn_vo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return BookStockResponse(isbn=str(isbn_vo), available_count=stock.available_count)


# ── GET /books/{isbn} ─────────────────────────────────────────────────────────
# WICHTIG: Muss NACH /books/{isbn}/availability und /books/{isbn}/return stehen.

@router.get("/books/{isbn}", response_model=BookResponse)
async def get_book(
    isbn: str,
    book_repo: BookRepository = Depends(get_book_repo),
) -> BookResponse:
    """Gibt ein einzelnes Buch per ISBN zurück (CAT-5).

    Args:
        isbn: ISBN-Zeichenkette aus dem URL-Pfad.
        book_repo: Repository für Buchoperationen.

    Returns:
        BookResponse mit allen Metadaten des Buches.

    Raises:
        HTTPException: 404 wenn das Buch nicht gefunden wurde.
        HTTPException: 422 wenn die ISBN ungültig ist.
    """
    try:
        isbn_vo = Isbn(isbn)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    use_case = GetBookUseCase(book_repo)
    try:
        book = await use_case.execute(isbn_vo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return BookResponse(
        isbn=str(book.isbn),
        title=book.title,
        author=book.author,
        genre=book.genre,
        description=book.description,
    )

