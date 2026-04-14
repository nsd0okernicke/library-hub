"""Catalog Service – FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging

import aio_pika
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.application.reserve_book_use_case import ReserveBookUseCase
from catalog.application.return_book_use_case import ReturnBookUseCase
from catalog.infrastructure.api.routers.books_router import (
    get_book_repo,
    get_stock_repo,
    router as books_router,
)
from catalog.infrastructure.config.settings import get_settings
from catalog.infrastructure.db.models import Base
from catalog.infrastructure.db.session import engine, get_session, AsyncSessionLocal
from catalog.infrastructure.db.sqlalchemy_book_repository import SqlAlchemyBookRepository
from catalog.infrastructure.db.sqlalchemy_book_stock_repository import SqlAlchemyBookStockRepository
from catalog.infrastructure.messaging.rabbitmq_consumer import RabbitmqConsumer
from catalog.infrastructure.messaging.rabbitmq_publisher import RabbitmqPublisher

logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
    """Create DB tables and start RabbitMQ consumer on startup."""
    settings = get_settings()

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Connect to RabbitMQ and start consumer
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        publisher = RabbitmqPublisher(exchange=exchange, exchange_name=settings.rabbitmq_exchange)

        # Consumer: use a per-message session factory so each message gets its own DB session
        async def _handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with AsyncSessionLocal() as session:
                stock_repo = SqlAlchemyBookStockRepository(session)
                reserve_uc = ReserveBookUseCase(stock_repo=stock_repo, publisher=publisher)
                return_uc = ReturnBookUseCase(stock_repo=stock_repo)
                consumer = RabbitmqConsumer(reserve_use_case=reserve_uc, return_use_case=return_uc)
                await consumer.handle_message(message)

        for queue_name, routing_key in [
            (settings.rabbitmq_queue_loan_requested, "book.loan.requested"),
            (settings.rabbitmq_queue_book_returned, "book.returned"),
        ]:
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=routing_key)
            await queue.consume(_handle_message)

        logger.info("Catalog: RabbitMQ consumer started")
        yield
        await connection.close()
        logger.info("Catalog: RabbitMQ connection closed")

    except Exception as exc:
        logger.warning("Catalog: RabbitMQ not available – running without messaging: %s", exc)
        yield

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="LibraryHub – Catalog Service",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "Manages the book catalogue and stock availability for the LibraryHub system.\n\n"
        "## Features\n"
        "- Add books with metadata and initial stock\n"
        "- Search and retrieve books by ISBN\n"
        "- Check real-time stock availability\n"
        "- Process book returns\n\n"
        "## Event-driven integration\n"
        "Publishes `BookReserved` / `BookOutOfStock` events and consumes "
        "`BookLoanRequested` / `BookReturned` events via RabbitMQ."
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
            "name": "books",
            "description": "Book catalogue operations – search, create, retrieve and return books.",
        },
        {
            "name": "health",
            "description": "Service health check.",
        },
    ],
)


# ── Production dependency overrides ──────────────────────────────────────────

def _prod_book_repo(  # pragma: no cover
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyBookRepository:
    """Production BookRepository implementation (SQLAlchemy)."""
    return SqlAlchemyBookRepository(session)


def _prod_stock_repo(  # pragma: no cover
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyBookStockRepository:
    """Production BookStockRepository implementation (SQLAlchemy)."""
    return SqlAlchemyBookStockRepository(session)


app.dependency_overrides[get_book_repo] = _prod_book_repo
app.dependency_overrides[get_stock_repo] = _prod_stock_repo

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(books_router, tags=["books"])


# ── Health ────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    response_description="Service status and name.",
)
async def health() -> dict[str, str]:
    """Return the current health status of the Catalog Service.

    Returns:
        A dict with ``status`` and ``service`` keys.
    """
    return {"status": "ok", "service": "catalog-service"}
