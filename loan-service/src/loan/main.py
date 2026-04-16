"""Loan Service – FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aio_pika
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from loan.application.activate_loan_use_case import ActivateLoanUseCase
from loan.application.reject_loan_use_case import RejectLoanUseCase
from loan.infrastructure.api.routers.loans_router import (
    get_loan_repo,
    get_publisher,
)
from loan.infrastructure.api.routers.loans_router import (
    router as loans_router,
)
from loan.infrastructure.api.routers.users_router import (
    get_user_repo,
)
from loan.infrastructure.api.routers.users_router import (
    router as users_router,
)
from loan.infrastructure.config.settings import get_settings
from loan.infrastructure.db.models import Base
from loan.infrastructure.db.session import AsyncSessionLocal, engine, get_session
from loan.infrastructure.db.sqlalchemy_loan_repository import SqlAlchemyLoanRepository
from loan.infrastructure.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from loan.infrastructure.messaging.logging_publisher import LoggingMessagePublisher
from loan.infrastructure.messaging.rabbitmq_consumer import RabbitmqConsumer
from loan.infrastructure.messaging.rabbitmq_publisher import RabbitmqPublisher

logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
    """Create DB tables, start RabbitMQ consumer and wire real publisher on startup."""
    settings = get_settings()

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Connect to RabbitMQ – wire real publisher and start consumer
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        real_publisher = RabbitmqPublisher(
            exchange=exchange, exchange_name=settings.rabbitmq_exchange
        )

        # Override publisher dependency with real RabbitMQ publisher
        app.dependency_overrides[get_publisher] = lambda: real_publisher

        # Consumer: use a per-message session factory so each message gets its own DB session
        async def _handle_message(
            message: aio_pika.abc.AbstractIncomingMessage,
        ) -> None:
            async with AsyncSessionLocal() as session:
                loan_repo = SqlAlchemyLoanRepository(session)
                activate_uc = ActivateLoanUseCase(loan_repo=loan_repo)
                reject_uc = RejectLoanUseCase(loan_repo=loan_repo)
                consumer = RabbitmqConsumer(
                    activate_use_case=activate_uc, reject_use_case=reject_uc
                )
                await consumer.handle_message(message)

        for queue_name, routing_key in [
            (settings.rabbitmq_queue_book_reserved, "book.reserved"),
            (settings.rabbitmq_queue_book_out_of_stock, "book.out_of_stock"),
        ]:
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=routing_key)
            await queue.consume(_handle_message)

        logger.info("Loan: RabbitMQ consumer started")
        yield
        await connection.close()
        logger.info("Loan: RabbitMQ connection closed")

    except Exception as exc:
        logger.warning(
            "Loan: RabbitMQ not available – running without messaging: %s", exc
        )
        yield


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="LibraryHub – Loan Service",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "Manages loan transactions and user registration for the LibraryHub system.\n\n"
        "## Features\n"
        "- Register new library users\n"
        "- Request, activate, reject and return book loans\n"
        "- List loans per user and overdue loans\n\n"
        "## Event-driven integration\n"
        "Publishes `BookLoanRequested` / `BookReturned` events and consumes "
        "`BookReserved` / `BookOutOfStock` events via RabbitMQ."
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
            "name": "users",
            "description": "User registration and management.",
        },
        {
            "name": "loans",
            "description": (
                "Loan lifecycle operations – request, activate, reject, "
                "return and query loans."
            ),
        },
        {
            "name": "health",
            "description": "Service health check.",
        },
    ],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(loans_router, tags=["loans"])
app.include_router(users_router, tags=["users"])


# ── Production dependency overrides ──────────────────────────────────────────


def _prod_user_repo(  # pragma: no cover
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyUserRepository:
    """Production UserRepository implementation (SQLAlchemy)."""
    return SqlAlchemyUserRepository(session)


def _prod_loan_repo(  # pragma: no cover
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyLoanRepository:
    """Production LoanRepository implementation (SQLAlchemy)."""
    return SqlAlchemyLoanRepository(session)


def _prod_publisher() -> LoggingMessagePublisher:  # pragma: no cover
    """Development MessagePublisher (logs instead of sending to RabbitMQ)."""
    return LoggingMessagePublisher()


app.dependency_overrides[get_user_repo] = _prod_user_repo
app.dependency_overrides[get_loan_repo] = _prod_loan_repo
app.dependency_overrides[get_publisher] = _prod_publisher


# ── Health ────────────────────────────────────────────────────────────────────


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    response_description="Service status and name.",
)
async def health() -> dict[str, str]:
    """Return the current health status of the Loan Service.

    Returns:
        A dict with ``status`` and ``service`` keys.
    """
    return {"status": "ok", "service": "loan-service"}
